(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.TourDemo = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  // Adapted from the owned offline ads-config proof: consent, safe schema, deduplication.
  // No transport, cookies, localStorage, Google/Meta calls or commercial transactions.
  function createTracker() {
    const events = [], seen = new Set();
    const fields = new Set(['event_id','event_name','tour_id','people','value','currency','analytics_consent']);
    return {
      get events() { return events.map(e => ({...e})); },
      ingest(e) {
        let reason = null;
        if (!e || e.analytics_consent !== true) reason = 'consent_denied';
        else if (!e.event_id || typeof e.event_id !== 'string' || !/^[a-zA-Z0-9_-]{1,80}$/.test(e.event_id)) reason = 'event_id_missing';
        else if (Object.keys(e).some(k => !fields.has(k))) reason = 'unexpected_fields';
        else if (e.event_name !== 'request_booking') reason = 'event_name_invalid';
        else if (!['motlawa','stare-miasto'].includes(e.tour_id)) reason = 'tour_invalid';
        else if (!Number.isInteger(e.people) || e.people < 1 || e.people > 8) reason = 'people_invalid';
        else if (e.currency !== 'PLN') reason = 'currency_mismatch';
        else if (e.value !== 0) reason = 'value_invalid';
        else if (seen.has(e.event_id)) reason = 'duplicate';
        if (reason) return {accepted:false,reason};
        seen.add(e.event_id);events.push({...e});return {accepted:true,reason:'accepted'};
      }
    };
  }
  return { createTracker };
});
