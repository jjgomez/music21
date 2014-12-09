define(['notebook/js/main', 'services/kernels/kernel', 'notebook/js/notebook', 
         'widgets/js/init','base/js/utils', 'bootstraptour'], 
        function() {
	getData = function (data) {
        console.log('data', data);
    };
    handle_output = function (out){
        // thanks to
        // http://jakevdp.github.io/blog/2013/06/01/ipython-notebook-javascript-python-communication/
        var res = null;

        // if output is a print statement
        // v3 has field "text" if out message is a stream
        if(out.msg_type === "stream"){
           res = out.content.text;
        }
        // if output is a python object
        // v3 no longer uses "pyout". uses excute_result as type
        else if(out.msg_type === "execute_result"){
           res = out.content.data["text/plain"];
        }
        // if output is a python error
        // v3 no longer "pyerr". just "error"
        else if (out.msg_type == "error"){
           res = out.content.ename + ": " + out.content.evalue;
        }
        // if output is something we haven't thought of
        else {
           res = "[out type not implemented]";  
        }
        return res;
    };
    exec_code = function (messagedCodeInput, outputCallback){
   	    console.log('exec_code', messagedCodeInput);
   	    var kernel = IPython.notebook.kernel;
   	    //console.log(IPython);
   	    //console.log(kernel.execute);
   	    //console.log(kernel.send_shell_message);
   	 	//console.log(kernel.channels.shell.send);
        if (outputCallback === undefined) {
       	  outputCallback = getData;
        }
        
        var callbacks = {};
        /*if (parseInt(IPython.version.slice(0,1)) < 2) {
            callbacks = {'output' : function (out) { var data = handle_output(out); 
                        outputCallback(data);
               } 
            };
        } else {*/
            callbacks = { 'iopub' : {'output' : function (out) {
            	//var data = handle_output(out);
            	var res = null;
            	console.log(out);
            	if(out.msg_type === 'error'){
            		exec_code('x=0');
            		res = 0;
            	} else if(out.msg_type === "execute_result"){
                    res = out.content.data["text/plain"];
                }
            	outputCallback(res);
            } } };
            
        //}
        var msg_id = kernel.execute(messagedCodeInput, callbacks, {silent:false});
        //console.log(msg_id);
    };
    waitForKernel = function () {
   		if (IPython.notebook !== undefined) {
   			console.log("second round");
   			if (IPython.notebook.kernel !== null && IPython.notebook.kernel.is_connected()) {
	   			console.log(IPython.notebook);
	            console.log('all loaded...waiting 50 more ms');
	   			setTimeout(startLocal, 50, true);
   			} else {
   	   		    console.log('still waiting');
   	   			setTimeout(waitForKernel, 100, true);
   	   		}
   		} else {
   		    console.log('still waiting');
   			setTimeout(waitForKernel, 100, true);
   		}
    };
    changePython = function () {
        var val = this.value; // HTMLInput
        exec_code(val, function(data) { $('#pyOutput').text(data); });
    }
    startLocal = function () {
   	    $(document).add('*').off();
   	    exec_code('');
		var $main = $("<div id='pyjsMain'>" + 
		    "Counter</div>");
	    $main.css('font-size', '40px').css('margin','20px 20px 20px 20px').css('line-height', '50px');
	    exec_code('x',function(data){
	    	$main.append("<div id='inc'>"+data+"</div>");
	    	var $button = $("<button type='button'>Increment</button>");
	    	$button.click(function(event){
	    		exec_code('x+=1');
	    		exec_code('x',function(data){
	    			console.log('Now is '+data);
	    			$('#inc').text(data);
	    		})
	    	});
	    	$main.append($button);
	        $('body').prepend($main);
	        
	    });
   	    IPython.notebook.notebook_name = newTitle + '.ABCDE';
   	    IPython.save_widget.update_document_title();
    };
    console.log('about to wait...');   
    var newTitle = "Python to Javascript Mapping via IPython Notebook";  // title keeps returning    
    waitForKernel();
});