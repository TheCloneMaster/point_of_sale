function openerp_proxy_device(instance,module){
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    module.ProxyDevice  = instance.web.Class.extend(openerp.PropertiesMixin,{
        init: function(parent,options){
            openerp.PropertiesMixin.init.call(this,parent);
            var self = this;
            options = options || {};
            url = options.url || 'http://localhost:8071';

            this.pos = parent;

            this.weighting = false;
            this.debug_weight = 0;
            this.use_debug_weight = false;

            this.paying = false;
            this.default_payment_status = {
                status: 'waiting',
                message: '',
                payment_method: undefined,
                receipt_client: undefined,
                receipt_shop:   undefined,
            };
            this.custom_payment_status = this.default_payment_status;

            this.receipt_queue = [];

            this.notifications = {};
            this.bypass_proxy = false;

            this.connection = null;
            this.host       = '';
            this.keptalive  = false;

            this.set('status',{});

            this.set_connection_status('disconnected');

            this.on('change:status',this,function(eh,status){
                status = status.newValue;
                if(status.status === 'connected'){
                    self.print_receipt();
                }
            });

            window.hw_proxy = this;
        },
        set_connection_status: function(status,drivers){
            oldstatus = this.get('status');
            newstatus = {};
            newstatus.status = status;
            newstatus.drivers = status === 'disconnected' ? {} : oldstatus.drivers;
            newstatus.drivers = drivers ? drivers : newstatus.drivers;
            this.set('status',newstatus);
        },
        disconnect: function(){
            if(this.get('status').status !== 'disconnected'){
                this.connection.destroy();
                this.set_connection_status('disconnected');
            }
        },

        // connects to the specified url
        connect: function(url){
            var self = this;
            this.connection = new instance.web.Session(undefined,url, { use_cors: true});
            this.host   = url;
            this.set_connection_status('connecting',{});

            return this.message('handshake').then(function(response){
                    if(response){
                        self.set_connection_status('connected');
                        localStorage['hw_proxy_url'] = url;
                        console.log('Connected');
                        //self.keepalive();
                    }else{
                        self.set_connection_status('disconnected');
                        console.error('Connection refused by the Proxy');
                    }
                },function(){
                    self.set_connection_status('disconnected');
                    console.error('Could not connect to the Proxy');
                });
        },
        message : function(name,params){
            var callbacks = this.notifications[name] || [];
            for(var i = 0; i < callbacks.length; i++){
                callbacks[i](params);
            }

            if(this.get('status').status !== 'disconnected'){
                return this.connection.rpc('/hw_proxy/' + name, params || {});
            }else{
                return (new $.Deferred()).reject();
            }
        },
        /*
         * ask the printer to print a receipt
         */
        print_receipt: function(receipt){
            var self = this;
            if(receipt){
                this.receipt_queue.push(receipt);
            }
            var aborted = false;
            function send_printing_job(){
                if (self.receipt_queue.length > 0){
                    var r = self.receipt_queue.shift();
                    self.message('print_xml_receipt',{ receipt: r },{ timeout: 5000 })
                        .then(function(){
                            send_printing_job();
                        },function(error){
                            if (error) {
//                                self.pos.pos_widget.screen_selector.show_popup('error-traceback',{
//                                    'message': _t('Printing Error: ') + error.data.message,
//                                    'comment': error.data.debug,
//                                });
                                console.log("Error de impresion")
                                return;
                            }
                            self.receipt_queue.unshift(r)
                        });
                }
            }
            send_printing_job();
        },

        // asks the proxy to log some information, as with the debug.log you can provide several arguments.
        log: function(){
            return this.message('log',{'arguments': _.toArray(arguments)});
        },

    });
};
