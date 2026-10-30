/* R2.0.6 — Premiere CEP ExtendScript Project Panel audit. READ ONLY.
 * Uses Premiere's documented ProjectItem DOM; never QE, no timeline writes.
 * Preview output contains local media paths, therefore save ONLY under the
 * workstation's private D:\AI-Video-Editor\Temp tree. Never upload to GitHub.
 */
if (typeof $ === 'undefined') { $ = {}; }
$._AIVE_R206_SCAN_ = (function() {
    var MAX_NODES = 50000, MAX_DEPTH = 50;
    function fail(msg) { throw Error('R206_SCAN: ' + msg); }
    function txt(s) { return String(s === null || s === undefined ? '' : s); }
    function kind(p) {
        var t = p.type;
        if (t === 2 || t === 3 || t === 'BIN' || t === 'ROOT') return 'bin';
        if (t === 1 || t === 4 || t === 'CLIP' || t === 'FILE') return 'media';
        return 'unknown';
    }
    function safe(fn, fallback) { try { return fn(); } catch (ignored) { return fallback; } }
    function convert(p, depth, tracker) {
        tracker.nodes++;
        if (tracker.nodes > MAX_NODES || depth > MAX_DEPTH) fail('Project Panel scan limit');
        if (!p) fail('Invalid Project Item');
        var name = txt(p.name), type = kind(p);
        if (!name) fail('Project Item without name');
        var item = { name: name, type: type };
        var nodeId = safe(function(){ return txt(p.nodeId); }, '');
        if (nodeId) item.nodeId = nodeId;
        if (type === 'bin') {
            var ch = safe(function(){return p.children;},null);
            if (!ch || typeof ch.numItems !== 'number') fail('Unreadable bin: ' + name);
            item.children = [];
            for (var i = 0; i < ch.numItems; i++) {
                item.children.push(convert(ch[i], depth + 1, tracker));
            }
        } else if (type === 'media') {
            var isSeq = safe(function(){ return typeof p.isSequence === 'function' && p.isSequence(); },false);
            if (isSeq) item.type = 'sequence';
            else {
                var isOffline = safe(function() {
                    return typeof p.isOffline === 'function' ? p.isOffline() : null;
                }, null);
                item.offline = (typeof isOffline === 'boolean') ? isOffline : null;
                item.mediaPath = safe(function() {
                    return typeof p.getMediaPath === 'function' ? txt(p.getMediaPath()) : '';
                }, '');
            }
        }
        return item;
    }
    function scan() {
        try {
            if (typeof app === 'undefined' || !app.project || !app.project.rootItem)
                fail('No Premiere project');
            var root = app.project.rootItem, tracker = {nodes: 0};
            var converted = convert(root, 0, tracker);
            if (converted.type !== 'bin') fail('Invalid project root');
            return JSON.stringify({ok:true, inventory: {
                schema:'aive-r206-project-panel-v1',
                items:converted.children
            }, nodeCount:tracker.nodes});
        } catch (e) {
            return JSON.stringify({ok:false, message:txt(e && e.message ? e.message : e)});
        }
    }
    return {scan:scan};
}());
