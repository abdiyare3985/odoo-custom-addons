odoo.define('utility.select_meter_info_page', function (require) {
    'use strict';

    const FormController = require('web.FormController');

    FormController.include({
        _onLoad: function () {
            this._super.apply(this, arguments);

            // Select the first page (Meter Info) in the notebook
            const notebook = this.$el.find('.o_notebook');
            if (notebook.length) {
                const firstPage = notebook.find('.o_notebook_page:first');
                if (firstPage.length) {
                    firstPage.click();
                }
            }
        },
    });
});