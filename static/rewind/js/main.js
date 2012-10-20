$(document).ready((function (undefined) {
    $('#about')
        .popover({
            placement: 'leftbottom',
            html: true,
            content: function () {
                return $('#popover_content').html();
            }
        })
        .click(function (event) {
            event.preventDefault();
        });

    if (!$.cookie('showed-popup')) {
        $('#about').popover('show');
        $.cookie('showed-popup', 1);
    }

    $(document).on('click', '.close', function() {
        $('#about').popover('hide');
    });
    // $('.close').click(function() {
    // });
    key('escape', function(){ $('#about').popover('hide'); });

    var api = '/api/v1/pages';
    var requesting = {};
    var buffer = 200;
    var currentPage, currentIdx;
    var $content = $('.content');

     // get the first key
    var maxPageIdx;
    for (var _i in pages) {
        if (pages.hasOwnProperty(_i)) {
            maxPageIdx = parseInt(_i, 10);
            break;
        }
    }

    // load templates from DOM
    var page_tpl = new EJS({ text: $('#page_tpl').html() });
    var post_tpl = new EJS({ text: $('#post_tpl').html() });

       function pageChunk (index, delta) {
        // return the url to request for this index
        delta = delta || 0;
        var floored = (Math.floor(index/buffer) + delta) * buffer;
        // make sure we dont request over maxPageIdx so we can properly cache response chunks
        var spec = {page: 0, idx: {'$gte': Math.min(maxPageIdx, floored),
                                   '$lt': Math.min(maxPageIdx+1, floored)+buffer}};
        return api + "?limit=" + buffer + "&spec=" + JSON.stringify(spec);
    }

    function renderPage(page) {
        if (page.rendered)
            return page.rendered;
        var posts = page.posts;
        var rows = [];
        var posDelta = page.page ? currentPage.posts.length : 0;
        for (var i=0;i<posts.length;i++) {
            var post = posts[i];
            post.pos += posDelta;
            rows.push(post_tpl.render(post));
        }
        page.rendered_posts = rows.join('');
        page.rendered = page_tpl.render(page);
        return page.rendered;
    }

    function formatDate (date) {
        d = moment.utc(date).local();
        return d.format("MMM Do YYYY, h:mma");
    }

    function ensureRequest (url) {
        if (requesting[url] === undefined) {
            // create a new request and chuck its deferred into the map
            requesting[url] = $.getJSON(url);
        }
    }

    function setContent(index, force) {
        if (!force &&
            (index > maxPageIdx || index < 0)) {
            return false;
        }
        // ensure we have the surrounding stuff
        var url = pageChunk(index);
        ensureRequest(url);
        var newPage = pages[index];
        if (newPage !== undefined) {
            if ($slider.slider('value') !== index) {
                return false;
            }
            var renderedPage = renderPage(newPage);
            $content.html(renderedPage);
            var date = formatDate(newPage.created_at);
            $('#date').text(date);
            currentIdx = index;
            currentPage = newPage;
        } else {
            // kay we dont have the page
            var callback = function (data) {
                // store the new pages
                var newPages = data.results;
                for (var i=0;i<newPages.length;i++) {
                    var page = newPages[i];
                    pages[page.idx] = page;
                }
                if (pages[index] === undefined) {
                    // uh oh we didn't get the page we requested
                    var apology = $('<h4>Unable to fetch page</h4>').css('position','absolute').position({of: $content});
                    $content.html(apology);
                } else {
                    setContent(index, force);
                }
            };
            // also buffer some more
            ensureRequest(pageChunk(index, 1));
            ensureRequest(pageChunk(index, -1));
            requesting[url]
                .done(callback, function() {  });
        }
    }

    function setSlider (pos) {
        $slider.slider('value', pos);
        setContent(pos);
    }

    function moveSlider(delta) {
        var newval = Math.max(0, Math.min(maxPageIdx, $slider.slider('value') + delta));
        setSlider(newval);
    }

    var $slider = $('<div id="slider"></div>');
    $slider.appendTo($('.top')).slider({
        value: maxPageIdx,
        max: maxPageIdx,
        create: function () {
            setContent(maxPageIdx, true);
        },
        slide: function (event, ui) {
            setSlider(ui.value);
        }
    });

    var hours = maxPageIdx / 6;
    var twohours = hours / 2;
    var rightPerc = 100 / twohours;
    for (var j=1;j<twohours;j++) {
        var cls = j % 12 ? 'twohour' : 'day';
        $('<div/>', {'class': 'mark ' + cls })
            .css('right', rightPerc * j + '%')
            .appendTo($slider);
    }

    $(document).on('click','.more', function (){
        var $more = $('.more');
        var $spinner = $('<div/>').addClass('spinner').insertBefore($more);
        $more.css('visibility', 'hidden');
        $.getJSON(api, {spec: JSON.stringify({ page:1, idx:currentIdx })})
            .done(function (data) {
                var page = data.results[0];
                $(renderPage(page)).find('tr').insertAfter($('.lasttr').last());
            })
            .fail(function () {
                $('<p></p>').text('Unable to fetch second page').appendTo($content);
            })
            .always(function () {
                $more.closest('tr').remove();
            });
    });

    key(            'left', function(){ moveSlider(  -1); });
    key(           'right', function(){ moveSlider(   1); });
    key(       'ctrl+left', function(){ moveSlider( -12); });
    key(      'ctrl+right', function(){ moveSlider(  12); });
    key( 'ctrl+shift+left', function(){ moveSlider(-144); });
    key('ctrl+shift+right', function(){ moveSlider( 144); });

}).call(this));
