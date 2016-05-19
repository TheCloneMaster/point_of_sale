//openerp.account_invoice_print_by_proxy = function (instance) {
function openerp_print_pos_session(instance, module){
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    module.PosSession  = Backbone.Model.extend({
        initialize: function(attributes){
            return this;
        },
        print_pos_sessions: function(pos_sessions){
            var self = this;
            this.proxy_url = "http://localhost:8071"
            this.proxy = new module.ProxyDevice(this);
            this.proxy.connect(this.proxy_url)
            _.each(pos_sessions,function(pos_session){
                this.formato = 'XmlPosSession'
                self.proxy.print_receipt(QWeb.render(this.formato,{
                    receipt: pos_session, widget: self,
                }

                ));
            });
        },
        print_pos_session: function(pos_session_ids) {
            var self = this;
            new instance.web.Model('pos.session').call('export_for_printing',[pos_session_ids]).then(function(pos_session_receipt){
                self.print_pos_sessions(pos_session_receipt);
                return true;
            },function(err,event){
                event.preventDefault();
                console.log("Error")
            });
            return true
        },
    });
    debugger;
    instance.web.client_actions.add('print_action_pos_session2', 'instance.pos_session_print_by_proxy.action');
    instance.pos_session_print_by_proxy.action = function (instance, context) {
        this.pos_session_ids = []
        this.PosSession = new module.PosSession(this);

        if (context.context.pos_session_ids) this.pos_session_ids = context.context.pos_session_ids;
        this.PosSession.print_pos_session(this.pos_session_ids);
    };
};
