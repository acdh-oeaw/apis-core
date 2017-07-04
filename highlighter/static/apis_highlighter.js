function find_related_object(elem, data) {
    for (i = 0; i < data.length; i++) {
        if (elem === data[i]['id']) {
            return data[i]
        }
    }
}

function get_menu_object(elem) {
    if (elem['kind'] == 'txt') {
    var res = '<a class="list-group-item">'+elem['name']+'</a>'}  
    else if (elem['kind'] == 'frm') {
        var res = '<a class="list-group-item" onclick=GetFormAjaxHighl("'+elem.api.api_endpoint+'")>'+elem['name']+'</a>'
    } else if (elem['kind'] == 'fn') {
        var res = '<a class="list-group-item" onclick='+elem.api.api_endpoint+'>'+elem['name']+'</a>'
    }
    
    return res
}

function updateObject(object, newValue, path){

  var stack = path.split('>');

  while (stack.length>1) {
    object = object[stack.shift()];
  }

  object[stack.shift()] = newValue;

}

function create_nested_menu(data, data_list) {
    //console.log(data)
    var res = ''
    for (x in data) {
        
       // res += '<li class="list-group-item">'+data_list[x]['name']
        if (data[x] instanceof Object && Object.keys(data[x]).length > 0) {
            res += '<a href="#HighlighterMenu'+data_list[x]['id']+'" class="list-group-item" data-toggle="collapse" data-parent="#HighlighterMenu'+data_list[x]['id']+'">'+data_list[x]['name']+'<i class="fa fa-caret-down"></i></a>\
              <div class="collapse list-group-submenu list-group-submenu-1" id="HighlighterMenu'+data_list[x]['id']+'">'
            res += create_nested_menu(data[x], data_list)
            res += '</div>'
        } else {
            //console.log(data_list[x])
            res += get_menu_object(data_list[x])
        }
    }
    return res
}

function create_apis_menu(data) {
    var lst_m = []
    var len = 0
    for (i = 0; i < data['menuentry_set'].length; i++) {
        //console.log(data['menuentry_set'][i]);
        var lst = []
        var elem = data['menuentry_set'][i]
        lst.push(elem)
        while (elem.parent) {
            if (!(elem.parent instanceof Object)) {
            elem.parent = find_related_object(elem.parent, data['menuentry_set'])}
            lst.push(elem.parent)
            elem = elem.parent
        }
        lst_m.push(lst.reverse());
        if (lst.length > len) {
            len = lst.length
        }
    }
    var menu_2 = {}
    var menu_2_lst = {}
    for (x = 0; x < lst_m.length; x++) {
            var s_n = menu_2
        for (u = 0; u < lst_m[x].length; u++) {
            if (!(lst_m[x][u]['id'] in menu_2_lst)) {
            s_n[lst_m[x][u]['id']] = {}
            menu_2_lst[lst_m[x][u]['id']] = lst_m[x][u]
            }
            s_n = s_n[lst_m[x][u]['id']]}
    }
    var menu_html = create_nested_menu(menu_2, menu_2_lst)
        menu_html += '</div>'
        menu_html = '<div class="panel list-group" id="accordion">' + menu_html
        return menu_html
}


function get_selected_text(txt_id) {
    var element = document.getElementById(txt_id);
    var start = 0, end = 0;
    var sel, range, priorRange;
    if (typeof window.getSelection != "undefined") {
        range = window.getSelection().getRangeAt(0);
        priorRange = range.cloneRange();
        priorRange.selectNodeContents(element);
        priorRange.setEnd(range.startContainer, range.startOffset);
        start = priorRange.toString().length;
        end = start + range.toString().length;
    } else if (typeof document.selection != "undefined" &&
            (sel = document.selection).type != "Control") {
        range = sel.createRange();
        priorRange = document.body.createTextRange();
        priorRange.moveToElementText(element);
        priorRange.setEndPoint("EndToStart", range);
        start = priorRange.text.length;
        end = start + range.text.length;
    }
    return {
        start: start,
        end: end,
        rect: range.getBoundingClientRect()
    };
};


function init_apis_highlighter(project_id, entity_id) {
    $.get("/api/HLProjects/"+project_id.toString()+"/", function(data){
        //menu = create_apis_menu(data.results[0])
        //$( "#test_menu" ).append(menu)
        //console.log(data)
        $.ApisHigh = {}
        $.ApisHigh.entity_id = entity_id
        var lst_class = []
        for (i=0; i < data['texthigh_set'].length; i++) {
           lst_class.push('.'+data['texthigh_set'][i]['text_class'])
        }
        var cl_2 = lst_class.join(', ')
        $(cl_2).bind('mouseup',function() {
        $.ApisHigh.selected_text = get_selected_text($(this).attr('id'))
        $.ApisHigh.selected_text.id = $(this).attr('id')
        })
        $(cl_2).tooltipster({
            content: 'Loading...',
            contentAsHTML: true,
            interactive: true,
            trigger: 'click',
            theme: 'tooltipster-light',
            side: ['bottom'],

        functionPosition: function(instance, helper, position){
            //console.log(position)
            position.coord.top = ($.ApisHigh.selected_text.rect.top + (position.distance + $.ApisHigh.selected_text.rect.height));
            position.coord.left = ($.ApisHigh.selected_text.rect.left - ((position.size.width/2)-($.ApisHigh.selected_text.rect.width/2)));
            position.target = $.ApisHigh.selected_text.rect.left + ($.ApisHigh.selected_text.rect.width/2)
            position.size.height = 'auto'
            //console.log(position.target)
            return position;
    },
        // 'instance' is basically the tooltip. More details in the "Object-oriented Tooltipster" section.
        functionBefore: function(instance, helper) {
            if ($.ApisHigh.high_complex){
                $.ApisHigh.high_complex.close();
            };
            if ($.ApisHigh.selected_text.start == $.ApisHigh.selected_text.end) {
                return false
            }
            var $origin = $(helper.origin);
            // we set a variable so the data is only loaded once via Ajax, not every time the tooltip opens
            if ($origin.data('loaded') !== true) {

                menu = create_apis_menu(data)

                    // call the 'content' method to update the content of our tooltip with the returned data
                    instance.content(menu);


                    // to remember that the data has been loaded
                    $origin.data('loaded', true);
                    $.ApisHigh.data_original = menu;

            } else {//console.log('fired');

            instance.content($.ApisHigh.data_original);}
            $.ApisHigh.tt_instance = instance
        },

    });

        //$.ApisHigh.tt_instance = $(cl_2).tooltipster('instance');
    })
}

