//  0: Column used to hold DataTables dt-control to hide/show child cells
//  1: 'name', Name
//  2: 'unit', Units
//  3: 'axis', Axes
//  4: 'description', Description
//  5: 'variable_type', Variable Type
//  6: 'vars_required_for_init', Req Init
//  7: 'vars_populated_by_init', Pop Init
//  8: 'vars_required_for_update' Req Update
//  9: 'vars_populated_by_first_update', Pop Update 1
// 10: 'vars_updated', Updated
// 10: 'used_by', Used By



document.addEventListener("DOMContentLoaded", function (event) {

    // Setup the variable table as a DataTable element
    var table = new DataTable('#variableTable', {
        // Using responsive to wrap the description, variable type and axes variables in
        // the responsive details child row, and simply present the information as a
        // string in that child: "description (type, axes: )"
        responsive: {
            details: {
                renderer: function (api, rowIdx, columns) {
                    return `${columns[4].data} (${columns[5].data}, axes: ${columns[3].data})`
                }
            }
        },
        // Style the displayed columns 
        // - can't order the child row dropdowns in column 0
        // - left align the variable names in column 1
        // - set widths manually: the default rendering uses equal splits and the
        //   datatables autoWidth option does not solve this
        columnDefs: [
            { targets: 0, orderable: false, width: "5%" },
            { targets: 1, className: 'dt-left' },
            { targets: 2, width: "20%" },
        ],
        // Sort by default on variable name
        order: [1, "asc"],
    });

    // Add logic to handle use of checkboxes to select row subsets.
    $('input:checkbox').on('change', function () {

        // Build a regex filter for model names in the Used By column, using | to or the
        // selected values
        var models = $('input:checkbox[name="models"]:checked').map(function () {
            return this.value;
        }).get().join('|');

        // Apply the model name regex filter to Used By (column 11).
        table.column(11).search(positions, true, false, false).draw(false);

        // TODO Need to apply other filters

    });

    // Style the responsive child rows - these are generated on the fly by DataTables
    // so applying styling via CSS does not work, so this JS is simply to add a left
    // aligned text class to the elements when they are exposed.
    $('#variableTable').on('click', 'td.dtr-control', function () {
        // Get the row that the control has been clicked on and select the next row,
        // which has just been revealed
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var next_row = tr.next()

        // Apply the class to the dt element within the row and 
        // style the background colour 
        if (row.child.isShown()) {
            var child_dt = next_row.children();
            child_dt.addClass('dt-left');
            child_dt[0].style.backgroundColor = 'gainsboro';
        }
    });

});