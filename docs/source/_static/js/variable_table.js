//  0: Column used to hold DataTables dt-control to hide/show child cells
//  1: 'name', Name
//  2: 'unit', Units
//  3: 'axis', Axes
//  4: 'description', Description
//  5: 'variable_type', Variable Type
//  6: 'vars_required_for_init', RI
//  7: 'vars_populated_by_init', PI
//  8: 'vars_required_for_update' RU
//  9: 'vars_populated_by_first_update', PU
// 10: 'vars_updated', Updated

// Hat tip to kthorngren on the DataTables API troubleshooting.
// https://datatables.net/forums/discussion/81581/implementing-a-custom-filter-with-or-columns-and-optional-column-selection

document.addEventListener("DOMContentLoaded", function (event) {

    // Page scoped variables
    var model_search_terms = [];  // Array of model search terms
    var model_search_regex = new RegExp(); // Regex OR search for selected models 
    var role_columns_selected = [];  // Array showing which variable row columns checked

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
        // - Do not allow ordering by the child row dropdowns in column 0
        // - Left align the variable names in column 1
        // - Set widths manually: the default rendering uses equal splits and the
        //   datatables autoWidth option does not solve this
        columnDefs: [
            { targets: 0, orderable: false, width: "5%" },
            { targets: 1, className: 'dt-left' },
            { targets: 2, width: "20%" },
        ],
        // Sort by default on variable name
        order: [1, "asc"],
        // Length options
        language: {
            lengthLabels: {
                '-1': 'Show all'
            }
        },
        lengthMenu: [10, 20, 50, 100, -1]
    });

    // Initialize a fixed search function that selects rows based on the model and
    // variable role checkboxes:
    // * No checkboxes filters no data
    // * Only role selectors selects rows that have a value for that role column
    // * Only model selectors selects rows where the model appears in any role
    // * Both selectors selects rows where the selected columns contain any of the
    //   selected models.

    table.search.fixed('orSearch', (row, data) => {

        // Variable to track if the cells in a data row match the selected models
        var model_matches = [];

        // Return the row if no checkboxes are selected
        if (
            (model_search_terms.length === 0) && !(role_columns_selected.some(Boolean))
        ) {
            return true;
        }

        // Extract the column data corresponding to the role selectors
        role_data = data.slice(6, 11);

        // Now, if no columns are selected, invert so all are selected, allowing model
        // selections with no role selections to subset to variables used for any role
        // in the model
        if (!role_columns_selected.some(Boolean)) {
            role_columns_selected = role_columns_selected.map(e => !e);
        }

        if (model_search_terms.length === 0) {
            // If no models are selected, then select cells containing _any_ data to
            // allow role selectors to drop to variables in specific roles
            model_matches = role_data.map(e => (e !== ""));
        } else {
            // Otherwise search using the OR regex for selected models
            model_matches = role_data.map(e => model_search_regex.test(e));
        }

        // Pairwise comparison of the two sets of selectors
        var selectors_agree = role_columns_selected.map(
            (element, index) => element && model_matches[index]
        );

        // If any cells are true in both selectors, return the row.
        return selectors_agree.some(Boolean);
    });



    // Function providing logic to set the fixed search conditions from the check boxes
    function CheckBoxes() {
        // Get the values from the selected model checkboxes
        model_search_terms = $('input:checkbox[name="models"]:checked').map(
            function () { return this.value; }).get();

        // Build the selected model names into an OR regex
        model_search_regex = new RegExp(model_search_terms.join('|'));

        // Populate the role_columns_selected array with the checked status of separate
        // role checkboxes
        role_columns_selected = [
            $("#vars_required_for_init").is(":checked"),
            $("#vars_populated_by_init").is(":checked"),
            $("#vars_required_for_update").is(":checked"),
            $("#vars_populated_by_first_update").is(":checked"),
            $("#vars_updated").is(":checked"),
        ];

        // Refresh the table, applying the fixed search
        table.draw();
    }

    // Trigger the CheckBoxes function whenever a user changes a checkbox
    $('input:checkbox').on('change', function () {
        CheckBoxes();
    });

    // Handle passing in preset checkboxes using parameters
    let params = new URLSearchParams(document.location.search);

    // Set model checkboxes from params if defined
    let url_models = params.get("models");
    if (url_models !== null) {
        url_models_array = url_models.split(",")
        url_models_array.forEach(model => $("#" + model).prop('checked', true));
    }

    // Set role checkboxes from params if defined
    let url_roles = params.get("roles");
    if (url_roles !== null) {
        url_roles_array = url_roles.split(",")
        url_roles_array.forEach(role => $("#" + role).prop('checked', true));
    }

    // If either param has been set, trigger the checkboxes to set the search conditions
    // and redraw the table
    if ((url_roles !== null) || (url_models !== null)) {
        CheckBoxes();
    }

});