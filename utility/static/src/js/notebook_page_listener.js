odoo.define('utility.notebook_page_listener', ['web.Widget'], function (require) {
    'use strict';

    const Widget = require('web.Widget');

    const NotebookPageListener = Widget.extend({
        selector: '.o_notebook',
        events: {
            'click .o_notebook_tab': '_onTabClick',
        },

        _onTabClick: function (event) {
            const tab = $(event.currentTarget);
            const tabName = tab.text().trim();

            if (tabName === 'Billing') {
                console.log('Billing page tabbed or opened');
                // Add your custom logic here
            }
        },
    });

    return NotebookPageListener;
});