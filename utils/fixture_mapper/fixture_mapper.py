"""Graph project test fixture usage.

This script will map the fixtures used by pytest and generate a graph of which fixtures
are used by which tests. It runs pytest twice to generate a list of the fixtures and
then the test setup plan. Together these can be used to get the fixture graph without
running the tests themselves.

Note that networkx is not currently a project or developer requirement for the project.
"""

import io
import subprocess

import networkx

# Read in the output of `pytest --fixtures > pytest_fixtures.log`
print("Running: pytest ../../tests --fixtures")
fixtures_output = subprocess.run(
    "pytest ../../tests --fixtures".split(" "), capture_output=True, text=True
)
fixture_lines = io.StringIO(fixtures_output.stdout).readlines()

# Reduce to the lines containing fixtures declared in the tests/ files and convert to a
# dictionary of fixture name and location
fixtures = [
    line.strip().split(" -- ") for line in fixture_lines if "-- ../../tests/" in line
]
fixtures_dict = {ky: vl for (ky, vl) in fixtures}

# Dump universal fixtures
fixtures_dict.pop("reset_module_registry")

# Read in the output of `pytest ../../tests --setup-plan`
print("Running: pytest ../../tests --setup-plan")
setup_output = subprocess.run(
    "pytest ../../tests --setup-plan".split(" "), capture_output=True, text=True
)
setup_lines = io.StringIO(setup_output.stdout).readlines()

tests: dict[str, dict] = {}
current_fixtures: dict[str, str] = {}
current_test = ""

for line in setup_lines:
    if line.startswith("../../tests/"):
        # save the fixture list associated with the previous test, checking that
        # previous parameterisations are using the same fixtures
        if current_test in tests:
            assert current_fixtures == tests[current_test]
        tests[current_test] = current_fixtures.copy()
        current_fixtures.clear()

        # Get the test name discarding any parameterisation label
        current_test = line.strip().split("[")[0]
    else:
        data = line.strip().split()
        if len(data) > 0 and data[0] == "SETUP" and data[2] in fixtures_dict:
            current_fixtures[data[2]] = fixtures_dict[data[2]]

# Write to text
with open("tests_fixtures.txt", "w") as outfile:
    for test_name, test_fixtures in tests.items():
        outfile.write(test_name + "\n")
        outfile.writelines([" * " + v + "\n" for v in test_fixtures])

print("Fixture report generated")

# Convert to graph
graph = networkx.Graph()

for test_name, test_fixtures in tests.items():
    graph.add_node(test_name, label=test_name, color="#0000FF")

    for fix_name, fix_loc in test_fixtures.items():
        graph.add_node(fix_name, label=fix_name, loc=fix_loc, color="#FF0000")
        graph.add_edge(test_name, fix_name)

networkx.write_graphml(graph, "tests_fixtures.graphml")

print(
    f"Fixture graph generated:\n"
    f"Tests found: {len(tests)}\n"
    f"Fixtures found: {len(fixtures)}\n"
    f"Number of fixture usages: {sum([len(v) for v in tests.values()])}\n"
)
