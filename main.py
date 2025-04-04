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

root_nodeId = driver.execute_cdp_cmd('DOM.getDocument', {})['root']['nodeId']

all_nodeIds = driver.execute_cdp_cmd('DOM.querySelectorAll', {
    'nodeId': root_nodeId,
    'selector': 'html > body *'
})['nodeIds']

nodes_with_listeners = {}
for nodeId in all_nodeIds:
    node = driver.execute_cdp_cmd('DOM.describeNode', {'nodeId': nodeId})
    remote_object = driver.execute_cdp_cmd('DOM.resolveNode', { 'nodeId': nodeId })
    events = driver.execute_cdp_cmd('DOMDebugger.getEventListeners',
                                       {'objectId': remote_object['object']['objectId']})
    if len(events['listeners']) > 0:
        print(node)
        print(events)
        print()
        print()


driver.quit()

