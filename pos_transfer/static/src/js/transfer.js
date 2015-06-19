openerp.pos_transfer = function(instance){
    var module   = instance.point_of_sale;
    var QWeb = instance.web.qweb;

    QWeb.add_template('/pos_transfer/static/src/xml/transfer.xml');

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();
            
            if(this.pos.config.iface_cashdrawer){
                return;
            }

            var transfer = $(QWeb.render('transferButton'));

            transfer.click(function(){
                var currentOrder = self.pos.get('selectedOrder');
                self.pos.push_order(currentOrder) 
                currentOrder.destroy();    //self.pos.get('selectedOrder') finish order and go back to scan screen
            });

            transfer.appendTo(this.$('.control-buttons'));
            this.$('.control-buttons').removeClass('oe_hidden');
        },
    });

};

