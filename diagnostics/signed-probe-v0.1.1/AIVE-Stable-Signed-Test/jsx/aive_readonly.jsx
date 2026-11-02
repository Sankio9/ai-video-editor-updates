/* AIVE STABLE SIGNED TEST — READ-ONLY Premiere handshake, no project modifications. */
$._AIVE_SIGNED_TEST = $._AIVE_SIGNED_TEST || {};
$._AIVE_SIGNED_TEST.getStatus = function () {
    function safe(x) {
        try { return String(x === null || x === undefined ? '' : x).replace(/[|\r\n]/g, ' ').substring(0, 150); }
        catch (e) { return '?'; }
    }
    try {
        var version = '?', project = 'NO_PROJECT', sequence = 'NO_SEQUENCE', tracks = 'N/A';
        try { version = safe(app.version); } catch (e) {}
        try {
            if (app.project) {
                project = safe(app.project.name || 'UNTITLED');
                if (app.project.activeSequence) {
                    sequence = safe(app.project.activeSequence.name || 'UNTITLED');
                    tracks = String(app.project.activeSequence.videoTracks.numTracks);
                }
            }
        } catch (e) { project = 'QUERY_UNAVAILABLE'; }
        return ['AIVE_SIGNED_TEST', 'PASS', version, project, sequence, tracks].join('|');
    } catch (e) { return 'AIVE_SIGNED_TEST|FAIL|' + safe(e); }
};
