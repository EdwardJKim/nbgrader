define(function(require) {
    var $ = require('jquery');
    var Jupyter = require('base/js/namespace');
    var LessonList = require('./lesson_list');

    var lesson_html = $([
        '<div id="lessons" class="tab-pane">',
        '  <div id="lessons_toolbar" class="row list_toolbar">',
        '    <div class="col-sm-8 no-padding">',
        '      <span id="lessons_list_info" class="toolbar_info">Released and downloaded lessons.</span>',
        '    </div>',
        '    <div class="col-sm-4 no-padding tree-buttons">',
        '      <span id="lessons_buttons" class="pull-right toolbar_buttons">',
        '      <button id="refresh_lessons_list" title="Refresh lessons list" class="btn btn-default btn-xs"><i class="fa fa-refresh"></i></button>',
        '      </span>',
        '    </div>',
        '  </div>',
        '  <div class="panel-group">',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Released lessons',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="released_lessons_list" class="list_container">',
        '          <div id="released_lessons_list_placeholder" class="row list_placeholder">',
        '            <div> There are no lessons to fetch. </div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '    <div class="panel panel-default">',
        '      <div class="panel-heading">',
        '        Downloaded lessons',
        '      </div>',
        '      <div class="panel-body">',
        '        <div id="fetched_lessons_list" class="list_container" role="tablist" aria-multiselectable="true">',
        '          <div id="fetched_lessons_list_placeholder" class="row list_placeholder">',
        '            <div> There are no downloaded lessons. </div>',
        '          </div>',
        '        </div>',
        '      </div>',
        '    </div>',
        '  </div>   ',
        '</div>'
    ].join('\n'));

   function load() {
        if (!Jupyter.notebook_list) return;
        var base_url = Jupyter.notebook_list.base_url;
        $('head').append(
            $('<link>')
            .attr('rel', 'stylesheet')
            .attr('type', 'text/css')
            .attr('href', base_url + 'nbextensions/lesson_list/lesson_list.css')
        );
        $(".tab-content").append(lesson_html);
        $("#tabs").append(
            $('<li>')
            .append(
                $('<a>')
                .attr('href', '#lessons')
                .attr('data-toggle', 'tab')
                .text('Lessons')
                .click(function (e) {
                    window.history.pushState(null, null, '#lessons');
                })
            )
        );
        var lesson_list = new LessonList.LessonList(
            '#released_lessons_list',
            '#fetched_lessons_list',
            '#submitted_lessons_list',
            {
                base_url: Jupyter.notebook_list.base_url,
                notebook_path: Jupyter.notebook_list.notebook_path,
            }
        );
        lesson_list.load_list();
    }
    return {
        load_ipython_extension: load
    };
});
