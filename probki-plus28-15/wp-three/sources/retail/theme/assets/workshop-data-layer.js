/* Local GTM dataLayer contract demonstration. No remote container is loaded. */
(function () {
  'use strict';
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  gtag('consent', 'default', {
    analytics_storage: 'denied', ad_storage: 'denied',
    ad_user_data: 'denied', ad_personalization: 'denied'
  });
  window.dataLayer.push({
    event: 'workshop_page_view',
    page_path: window.location.pathname,
    environment: 'local_demonstration',
    remote_tags_loaded: false
  });
  document.addEventListener('click', function (event) {
    var target = event.target.closest('a');
    if (target && target.classList.contains('wp-block-button__link')) {
      window.dataLayer.push({event: 'workshop_cta_click', link_path: target.getAttribute('href')});
    }
  });
  document.addEventListener('submit', function (event) {
    if (event.target.matches('form.checkout')) {
      window.dataLayer.push({event: 'workshop_checkout_submit', environment: 'local_demonstration'});
    }
  });
})();
