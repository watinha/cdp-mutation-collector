from selenium import webdriver


options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-feature=Translate')
options.add_argument('--disable-search-engine-choice-screen')

driver = webdriver.Remote(
        command_executor='http://172.17.0.1:1234', options=options)

driver.get('http://www.google.com')
driver.implicitly_wait(10)
driver.save_screenshot('screenshot.png')

driver.execute_script('''

window.mutations_observed = [];
var observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        var target = mutation.target;
        window.mutations_observed.push(target);
        if (mutation.addedNodes) {
            for (var i = 0; i < mutation.addedNodes.length; i++) {
                if (mutation.addedNodes[i].nodeType === 1)
                    window.mutations_observed.push(mutation.addedNodes[i]);
            };
        }

    });
});
observer.observe(document.body, {
    attributes: true,
    childList: true,
    subtree: true
});

''')

root_nodeId = driver.execute_cdp_cmd('DOM.getDocument', {})['root']['nodeId']

all_nodeIds = driver.execute_cdp_cmd('DOM.querySelectorAll', {
    'nodeId': root_nodeId,
    'selector': 'html > body *'
})['nodeIds']

event_types = ['blur', 'change', 'click', 'focus', 'input', 'keydown', 'keypress',
               'keyup', 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove']

nodes_with_listeners = []
for i, nodeId in enumerate(all_nodeIds):
    node = driver.execute_cdp_cmd('DOM.describeNode', {'nodeId': nodeId})
    remote_object = driver.execute_cdp_cmd('DOM.resolveNode', { 'nodeId': nodeId })
    events = driver.execute_cdp_cmd('DOMDebugger.getEventListeners',
                                       {'objectId': remote_object['object']['objectId']})

    node_events = []
    for ev in events['listeners']:
        if ev['type'] in event_types:
           node_events.append(ev['type'])
    if len(node_events) > 0:
        attributes = driver.execute_cdp_cmd('DOM.getAttributes', {'nodeId': nodeId})
        attributes_obj = {}
        for i in range(0, len(attributes['attributes']), 2):
            attributes_obj[attributes['attributes'][i]] = attributes['attributes'][i + 1]
        className = attributes_obj['class'] if 'class' in attributes_obj else ''

        driver.execute_cdp_cmd('DOM.setAttributeValue', {
            'nodeId': nodeId,
            'name': 'class',
            'value': f'{className} event-listener website-collector-{i}'
        })

        nodes_with_listeners.append({
            'node': node,
            'html': driver.execute_cdp_cmd(
                'DOM.getOuterHTML', {'nodeId': nodeId})['outerHTML'],
            'events': node_events
        })


l = driver.execute_script('''	

var list = window.mutations_observed;
window.mutations_observed = [];
return list;

''')

print(l)

driver.quit()


