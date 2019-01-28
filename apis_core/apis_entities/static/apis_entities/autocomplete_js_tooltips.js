function autocomplete_vis_coin(obj, elem_id) {
  var src = obj.data('apis-pic');
  $('#'+elem_id).append('<img src="'+src+'" width="200" height="200"/>');
  return
};

function autocomplete_vis_place(obj, elem_id) {
  $('body').append('<div class="autocomplete-vis-container" id="'+elem_id+'" style="display: hidden"><div  id="inner_'+elem_id+'" style="height: 250px; width: 250px; margin: 0; padding:0"></div></div>')
  var map = L.map('inner_'+elem_id, {
  center: [obj.data('lat'), obj.data('long')],
  zoom: 8,
  zoomControl: false});
  var tile_layer = L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}',
  {
    maxZoom: 8,
    id: 'mapbox.light',
    accessToken: 'pk.eyJ1Ijoic2VubmllcmVyIiwiYSI6ImNpbHk1YWV0bDAwZnB2dW01d2l1Y3phdmkifQ.OljQLEhqeAygai2y6VoSwQ'
}).addTo(map);
  console.log(obj.data('lat'));
  L.marker([obj.data('lat'), obj.data('long')]).addTo(map);
  //map.setView([obj.data('lat'), obj.data('long')], 8);
tile_layer.on('load', function() {
console.log('load fired');
	$(obj).tooltipster('content', $('#'+elem_id))
})
//return map
};

function autocomplete_vis_person(obj, elem_id) {
var t = '<p><ul style="list-style-type: none; padding: 0; margin: 0">'
	t += '<li><a href="'+obj.data('url')+'">go to entity</a></li>'
	t += '<li><b>Date of Birth:</b> '+obj.data('start')+'</li>'
	t += '<li><b>Date of Death:</b> '+obj.data('end')+'</li>'
	t += '<li><b>Place of Birth:</b> '+obj.data('birthplace')+'</li>'
	t += '</ul></p>'
 var elem2 =  $('body').append('<div class="autocomplete-vis-container" id="'+elem_id+'" style="max-height: 300px; width: 250px; display:hidden;">'+t+'</div>');
	$(obj).tooltipster('content', $('#'+elem_id));
}
