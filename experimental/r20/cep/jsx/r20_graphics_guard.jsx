/* R2.0 candidate: isolated safety gate. No modification of stable modules 01-05.
   Designed for ExtendScript ES3 and Node-based mocks. Do not publish as stable. */
var AIVE_R20Guard = (function () {
    var map = {'02': 2, '03': 3, '04': 4}; // 0-based Premiere video tracks
    function fail(msg) { throw new Error('R20_GUARD: ' + msg); }
    function validNumber(n) { return typeof n === 'number' && isFinite(n); }
    function trackFor(mod) {
        if (!Object.prototype.hasOwnProperty.call(map, mod)) fail('unknown module');
        return map[mod];
    }
    function checkPlan(p) {
        if (!p || p.schema !== 'aive-r20-graphics-v1') fail('wrong schema');
        var target = trackFor(p.module);
        if (p.mode !== 'independent') fail('synced mode handled by stable modules');
        if (!/^[a-f0-9]{64}$/.test(String(p.docx_sha256 || ''))) fail('DOCX SHA absent');
        if (!p.items || !p.items.length || p.items.length > 2000) fail('empty/oversized plan');
        if (p.module === '02' && p.timing !== 'SCRIPT_PREVIEW') fail('subtitles must say SCRIPT_PREVIEW');
        if (p.module !== '02' && p.timing !== 'SCRIPT_PREVIEW' && p.timing !== 'EDITORIAL_PREVIEW') fail('preview timing expected');
        var lastEnd = -1, lastGroup = null, groups = {}, seen = {};
        var separator = validNumber(p.separatorSeconds) ? p.separatorSeconds : 0.75;
        if (separator < 0 || separator > 2) fail('separator outside 0..2s');
        for (var i=0; i<p.items.length; i++) {
            var a = p.items[i];
            if (!a || typeof a.id !== 'string' || !a.id || seen[a.id]) fail('duplicate/missing item id');
            seen[a.id] = true;
            if (typeof a.groupId !== 'string' || !a.groupId) fail('missing group id');
            if (typeof a.text !== 'string' || !a.text.replace(/\s/g, '')) fail('empty text');
            if (!validNumber(a.startSeconds) || !validNumber(a.durationSeconds) ||
                a.startSeconds < 0 || a.durationSeconds < .12) fail('invalid item time');
            if (lastEnd > a.startSeconds + .0001) fail('overlapping planned items');
            if (lastEnd >= 0) {
                var gap = a.startSeconds - lastEnd;
                if (a.groupId === lastGroup && gap > .12) fail('space within block');
                if (a.groupId !== lastGroup && gap > separator + .12) fail('montage-sized gap not allowed');
            }
            if (p.module === '02' && a.text.length > 74) fail('subtitle over 74 chars');
            if (p.module === '03' && groups[a.groupId]) fail('multiple nametags in same editorial block');
            if (p.module === '04') {
                var lines = a.text.split(/\r?\n/);
                if (lines.length > 4) fail('carton over 4 lines');
                for (var k=0; k<lines.length; k++) if (lines[k].length > 33) fail('carton line over 33 characters');
            }
            groups[a.groupId] = true;
            lastGroup = a.groupId;
            lastEnd = a.startSeconds + a.durationSeconds;
        }
        return target;
    }
    function occupiedRanges(existing) {
        if (!existing || typeof existing.length !== 'number') fail('cannot scan clips');
        var arr = [];
        for (var i=0; i<existing.length; i++) {
            var a=existing[i];
            if (!validNumber(a.start) || !validNumber(a.end) || a.end < a.start) fail('invalid existing clip bounds');
            arr.push({name:String(a.name || ''), kind:String(a.kind || 'unknown'),
                      start:a.start, end:a.end, id:String(a.id || '')});
        }
        return arr;
    }
    function collide(p, existing) {
        var c=[];
        for (var i=0; i<p.items.length; i++) for (var j=0; j<existing.length; j++) {
            var x=p.items[i], y=existing[j];
            if (x.startSeconds < y.end - .001 && x.startSeconds + x.durationSeconds > y.start + .001)
                c.push({item:x.id, clip:y.name, clipId:y.id});
        }
        return c;
    }
    function inspect(p, snapshot) {
        var target=checkPlan(p);
        if (!snapshot || snapshot.sequenceId !== p.sequenceId) fail('sequence changed');
        if (snapshot.targetTrack !== target || snapshot.trackCount <= target) fail('target track missing');
        if (snapshot.lockState !== false) fail('target track locked or lock state unknown');
        var existing=occupiedRanges(snapshot.clips);
        var collisions=collide(p, existing);
        var blocked = collisions.length > 0 || (p.module === '04' && existing.length > 0);
        return {ok:!blocked, targetTrack:target, blocked:blocked,
            inventory:existing, collisions:collisions,
            choices:p.module === '04' && existing.length ?
                ['Suprascrie materialele de pe V5','Oprește, eliberez V5'] : [],
            reason:blocked ? (p.module === '04' ? 'V5_OCCUPIED' : 'COLLISION') : 'READY',
            timing:p.timing};
    }
    return {checkPlan:checkPlan, inspect:inspect, collide:collide, occupiedRanges:occupiedRanges};
}());
if (typeof module !== 'undefined' && module.exports) module.exports=AIVE_R20Guard;
