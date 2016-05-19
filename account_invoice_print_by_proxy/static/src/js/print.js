//openerp.account_invoice_print_by_proxy = function (instance) {
function openerp_print_invoice(instance, module){
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    module.Invoice  = Backbone.Model.extend({
        initialize: function(attributes){
            return this;
        },
        print_receipts: function(receipts){
            var self = this;
            this.proxy_url = "http://192.168.2.100:8069"
            this.proxy = new module.ProxyDevice(this);
            this.proxy.connect(this.proxy_url)
            _.each(receipts,function(receipt){
                this.formato = 'XmlInvoice'
                self.proxy.print_receipt(QWeb.render(this.formato,{
                    receipt: receipt, widget: self,
                }

                ));
            });
        },
        print_invoice: function(invoice_ids) {
            var self = this;
            new instance.web.Model('account.invoice').call('export_for_printing',[invoice_ids]).then(function(invoice_receipt){
                self.print_receipts(invoice_receipt);
                return true;
            },function(err,event){
                event.preventDefault();
                console.log("Error")
            });
            return true
        },
    });

    instance.web.client_actions.add('print_action_invoice', 'instance.account_invoice_print_by_proxy.action');
    instance.account_invoice_print_by_proxy.action = function (instance, context) {
        this.invoice_ids = []
        this.Invoice = new module.Invoice(this);

        if (context.context.invoice_ids) this.invoice_ids = context.context.invoice_ids;
        this.Invoice.print_invoice(this.invoice_ids);
    };
};
