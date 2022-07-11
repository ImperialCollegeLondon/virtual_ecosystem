# Building slides

The python notebooks in this directory are intended to be built as slides. Some of the
slides are supposed to be scrollable to include longer outputs. That is fine:

```bash
jupyter-nbconvert --to slides development_toolchain.md\
                  --SlidesExporter.reveal_scroll=True
```

The problem is then that the slides template is - I think - set up to expect only a
single cell in a scrolling slide, not a mix of text and code cells. The hacky way to
solve this is to edit the generated HTML to fix the Reveal slide width and alter the
scaling of the scroll box

```js
function(Reveal, RevealNotes){
    // Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
    Reveal.initialize({
        controls: true,
        progress: true,
        history: true,
        transition: "slide",
        slideNumber: "",
        plugins: [RevealNotes],
        width: 1200     // <<<<<<< Added width
    });

    var update = function(event){
        if(MathJax.Hub.getAllJax(Reveal.getCurrentSlide())){
        MathJax.Hub.Rerender(Reveal.getCurrentSlide());
        }
    };

    Reveal.addEventListener('slidechanged', update);

    function setScrollingSlide() {
        var scroll = true
        if (scroll === true) {
            var h = $('.reveal').height() * 0.80; // <<<<<<< Changed from * 90
            $('section.present').find('section')
            .filter(function() {
                return $(this).height() > h;
            })
            .css('height', 'calc(60vh)') // <<<<<<< changed from 'calc(95vh)'
            .css('overflow-y', 'scroll')
            .css('margin-top', '20px');
        }
    }

    // check and set the scrolling slide every time the slide change
    Reveal.addEventListener('slidechanged', setScrollingSlide);
}
```
