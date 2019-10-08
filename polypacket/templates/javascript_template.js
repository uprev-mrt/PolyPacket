function ${proto.prefix}_send_req(req, callback) {

   var full_url = "http://" + window.location.host + req.url + "?";

   //Remove all null fields from object
   for (var propName in req.packet) {
     if (req.packet[propName] === null || req.packet[propName] === undefined) {
       delete req.packet[propName];
     }
   }

   console.log("OUT >>> " + JSON.stringify(req.packet) );

   $.ajax({
       type: "POST",
       url: full_url,
       data: JSON.stringify(req.packet),
       cache: false,
       success: function(response){
         console.log(" IN <<< " + response);

         if(typeof callback === 'function'){
           callback(JSON.parse(response));
         };
       }
   });
}

function ${proto.prefix}_new_req()
{
  var req = {
    url: "/${proto.prefix}_service",
    packet: {
        packetType: "unkown"
    }};

    return req;
}

function ${proto.prefix}_sendPing(callback)
{
  var req = ${proto.prefix}_new_req();
  req.packet.packetType="Ping";

  ${proto.prefix}_send_req(req, callback);
}

% for packet in proto.packets:
%if not packet.standard:
/**
  *@brief sends ${packet.name} packet
  %for field in packet.fields:
  %if field.isRequired:
  *@param ${field.name} value to set ${field.name} field to
  %endif
  %endfor
  *@return ${proto.prefix}_status send attempt
  */
function ${proto.prefix}_send${packet.camel()}(\
  %for idx,field in enumerate(packet.fields):
  %if field.isRequired:
  ${field.name.lower()} , \
  %endif
  %endfor
  callback \
)
{
  var req = ${proto.prefix}_new_req();
  req.packet.packetType="${packet.name}";

  //set fields
  %for field in packet.fields:
  %if field.isRequired:
  req.packet.${field.name} = ${field.name.lower()};
  %endif
  %endfor

  //Send request
  ${proto.prefix}_send_req(req, callback);
}
%endif

% endfor
