load('ext://uibutton', 'cmd_button', 'text_input', 'location')

docker_compose('compose.yaml')

# Label resources for better organization
dc_resource('temporal', labels=['infra'])
dc_resource('tempo', labels=['infra'])
dc_resource('grafana', labels=['infra'])
dc_resource('worker', labels=['app'])

# --- Workflow trigger buttons ---

cmd_button('run-delivery',
    argv=['uv', 'run', 'python', '-m', 'temporal_planner.client', '--scenario', 'delivery'],
    resource='worker',
    icon_name='local_shipping',
    text='Run Delivery Scenario',
)

cmd_button('run-multi-package',
    argv=['uv', 'run', 'python', '-m', 'temporal_planner.client', '--scenario', 'multi'],
    resource='worker',
    icon_name='inventory_2',
    text='Run Multi-Package Scenario',
)

cmd_button('run-custom',
    argv=['sh', '-c', 'uv run python -m temporal_planner.client --scenario $SCENARIO'],
    resource='worker',
    icon_name='play_arrow',
    text='Run Custom Scenario',
    inputs=[text_input('SCENARIO', 'Scenario name (delivery or multi)')],
)

# --- Navigation links ---

local_resource(
    'temporal-ui',
    cmd='echo "Temporal UI: http://localhost:8233"',
    links=['http://localhost:8233'],
    labels=['links'],
)

local_resource(
    'grafana-ui',
    cmd='echo "Grafana: http://localhost:3000"',
    links=['http://localhost:3000'],
    labels=['links'],
)
