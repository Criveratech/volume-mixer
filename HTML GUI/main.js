
document.addEventListener("DOMContentLoaded", function(event) {
    
    //either a reverse proxied url or if you're running everything locally
    //just put ws://ip:port of the websocket server
    //important distinction between wss (secure, your server needs to serve https with a certificate)
    //and ws (HTTP on port 80, needs no certificate)
    let wss = null;
    let interval = null;
    //const wss = new WebSocket("wss://mydomain/wss");
    function connect(){
        if(wss){return}
        wss = new WebSocket("ws://192.168.178.20:8001");
        wss.onclose = function(){
            wss.close()
            wss = null;
            wss.terminate()
            interval = setInterval(connect,1000)
        }
        wss.onopen = function(){
            console.log("SUCESSFULY CONECCT")
            clearInterval(interval)
            wss.onmessage = function incoming(message) {
                
                parseJson(message.data,wss)
              //console.log('received: %s', message.data);
            };
        }
    }
    connect()
    
})

function parseJson(jsonString,wss){
    //if(jsonString.type != "")
    

    let processes = JSON.parse(jsonString)
    if(processes.type == "mixerUpdate"){

        let rootDiv = document.getElementById("volumesDiv")
        rootDiv.innerHTML=""
    
        processes.procs.forEach(element => {

            let volumeDiv = rootDiv.appendChild(document.createElement("div"));
            volumeDiv.classList.add('volume');

            let slider = volumeDiv.appendChild(document.createElement("input"));
            slider.setAttribute("class","sliders")
            slider.setAttribute("type","range")
            slider.setAttribute("min","1")
            slider.setAttribute("max","10000")
            slider.setAttribute("step","1")
            slider.setAttribute("value",element.volume*10000)
            slider.setAttribute("id",element.name)

            let volumeText = volumeDiv.appendChild(document.createElement("label"));
            volumeText.classList.add('test');
            volumeText.innerHTML=element.name;
            volumeText.setAttribute("for",element.name)
            
            
            

        // slider.style.width="100%"
        // slider.style.height="100px"
            slider.addEventListener("input",(e)=>{
                wss.send('{"type":"volume","name":"'+element.name+'","volume":'+e.target.value/10000+'}');
            })
        });
    }
}