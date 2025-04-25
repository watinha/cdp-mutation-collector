import sys, os

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By


_, url = sys.argv
domain = url.split('://')[1].split('/').pop()
results_dir = 'results'
browser_width = 1080
browser_height = 1080

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument(f'--window-size={browser_height},{browser_width}')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--remote-debugging-port=9222')
options.add_argument('--disable-extensions')
options.add_argument('--disable-feature=Translate')
options.add_argument('--disable-search-engine-choice-screen')

driver = webdriver.Remote(
        command_executor='http://172.17.0.1:1234', options=options)

print(f'Starting Chromium and opening {url}...')
driver.get(url)
driver.implicitly_wait(10)

print(f'Setting results directory in ./{results_dir}/{domain}...')
if not os.path.isdir(f'./{results_dir}/{domain}'):
    os.mkdir(f'./{results_dir}/{domain}')
driver.save_screenshot('./{results_dir}/{domain}/screenshot.png')

print('Setting up MutationObserver...')
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

print('Searching for event listeners...')
root_nodeId = driver.execute_cdp_cmd('DOM.getDocument', {})['root']['nodeId']

all_nodeIds = driver.execute_cdp_cmd('DOM.querySelectorAll', {
    'nodeId': root_nodeId,
    'selector': 'html > body *'
})['nodeIds']

event_types = [ 'click', 'focus', 'keydown', 'keypress', 
                'keyup', 'change', 'input', 'mouseover' ]
                #'blur', 'mousedown', 'mouseup', 'mouseout', 'mousemove']

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
            'className': f'.event-listener.website-collector-{i}',
            'html': driver.execute_cdp_cmd(
                'DOM.getOuterHTML', {'nodeId': nodeId})['outerHTML'],
            'events': node_events
        })

print(f'Found {len(nodes_with_listeners)} nodes with event listeners.')
print('Dispatching events, recording mutations and taking screenshots...')
for node in nodes_with_listeners:
    events = node['events']
    className = node['className']
    chain = ActionChains(driver)

    for event in events:
        try:
            target = driver.find_element(
                By.CSS_SELECTOR, className)

            rectangle = target.rect
            if target.is_displayed() == False or rectangle['width'] == 0 or rectangle['height'] == 0 or rectangle['x'] >= browser_width or rectangle['y'] == browser_height:
                print(f'Skipping {className} because it is not visible.')
                break

            ariaExpanded = target.get_attribute('aria-expanded')
            textContent = target.get_attribute('textContent')

            if event == 'mouseover':
                chain.move_to_element(target).pause(2).perform()
                driver.save_screenshot(f'./{results_dir}/{domain}/screenshot-{className}-hover.png')
            if (ariaExpanded is not None and ariaExpanded == 'false' and event == 'click') or event == 'focus':
                chain.move_to_element(target).pause(1).click().pause(2).perform()
                driver.save_screenshot(f'./{results_dir}/{domain}/screenshot-{className}-focus.png')
            if event == 'keydown' or event == 'keyup' or event == 'keypress' or event == 'change' or event == 'input':
                chain.move_to_element(target).send_keys('a').pause(2).perform()
                driver.save_screenshot(f'./{results_dir}/{domain}/screenshot-{className}-key.png')
        except Exception as e:
            print(e)
            break

        driver.implicitly_wait(3)
        js_get_target = f'let className = "{className}"; let target = document.querySelector(className);'
        list_of_mutations = driver.execute_script(js_get_target + '''

function count_words (el) {
    const childs = el.querySelectorAll('*');
    let childs_count = 0,
        word_count = 0;
    for (let i = 0; i < childs.length; i++) {
        const target = childs[i];
        if (target.children.length === 0) {
            childs_count++;
            word_count += target.textContent.split(' ').length;
        }
    }
    if (childs_count === 0) return 0;
    return word_count / childs_count;
}
function offset (el) {
    const rect = el.getBoundingClientRect(),
          win = el.ownerDocument.defaultView;
    return {
        top: rect.top + win.pageYOffset,
        left: rect.left + win.pageXOffset
    };
}
function dimension (el) {
    return {
        height: (el.offsetHeight ? el.offsetHeight : 0),
        width: (el.offsetWidth ? el.offsetWidth : 0)
    };
}
function landmark_parent (el) {
    if (!el)
        return false;
    const tagname = el.tagName.toLowerCase();
    if ((tagname === 'footer' || tagname === 'aside' || tagname === 'main' ||
        tagname === 'form' || tagname === 'header') && label_for(el))
        return tagname;
    if (tagname === 'nav' || tagname === 'section') {
        return tagname;
    }
    const role = el.getAttribute('role');
    if (role) {
        return role;
    }
    return landmark_parent (el.parentElement);
}
function label_for (el) {
    const labelledby = el.getAttribute('aria-labelledby'),
          label = el.getAttribute('aria-label'),
          title = el.getAttribute('title');

    if (labelledby || label || title) {
        return `${el.className} ${labelledby} ${label} ${title}`;
    }
    return false;
}
function get_xpath (target) {
    var xpath = '', tagName, parent = target.parentElement,
        index, children;
    while (parent != null) {
        tagName = target.tagName.toLowerCase();
        children = [].slice.call(parent.children);
        index = children.indexOf(target) + 1;
        xpath = '/' + tagName + '[' + index + ']' + xpath;
        target = parent;
        parent = target.parentElement;
    };
    return xpath;
}
function calculate_weighted_avg (el, attr_call, weight) {
   let childs = Array.from(el.children),
       weighted_sum = 0,
       size = childs.length;

    childs.forEach((child) => {
        const result = calculate_weighted_avg(child, attr_call, weight / 2);
        weighted_sum += attr_call(child) * weight + result.weighted_sum;
        size += result.size;
    });

    return { weighted_sum, size, weighted_avg: weighted_sum / size };
}
function get_all_features(el) {
    const position = offset(el);
    const tags = [
        'a', 'abbr', 'acronym', 'address', 'applet', 'area',
        'article', 'aside', 'audio', 'b', 'base', 'basefont',
        'bdi', 'bdo', 'big', 'blockquote', 'body', 'br', 'button',
        'canvas', 'caption', 'center', 'cite', 'code', 'col',
        'colgroup', 'data', 'datalist', 'dd', 'del', 'details',
        'dfn', 'dialog', 'dir', 'div', 'dl', 'dt', 'em', 'embed',
        'fieldset', 'figcaption', 'figure', 'font', 'footer',
        'form', 'frame', 'frameset',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head', 'header',
        'hr', 'html', 'i', 'iframe', 'img', 'input', 'ins', 'kbd',
        'label', 'legend', 'li', 'link', 'main', 'map', 'mark',
        'meta', 'meter', 'nav', 'noframes', 'noscript', 'object',
        'ol', 'optgroup', 'option', 'output', 'p', 'param',
        'picture', 'pre', 'progress', 'q', 'rp', 'rt', 'ruby',
        's', 'samp', 'script', 'section', 'select', 'small',
        'source', 'span', 'strike', 'strong', 'style', 'sub',
        'summary', 'sup', 'svg', 'table', 'tbody', 'td', 'template',
        'textarea', 'tfoot', 'th', 'thead', 'time', 'title', 'tr',
        'track', 'tt', 'u', 'ul', 'var', 'video', 'wbr'];

    let counter = {};
    tags.forEach((tag) => {
        counter[`${tag}_count`] = el.querySelectorAll(tag).length;
    });

    let averages = {};
    if (el.children.length > 0) {
        averages.avg_top = Array.from(el.children).reduce((acc, child) =>
                acc + (offset(child).top - position.top), 0) / el.children.length;
        averages.weighted_top = calculate_weighted_avg(el, (elem) =>
                offset(elem).top - position.top, 1).weighted_avg;
        averages.sd_top = Math.sqrt(Array.from(el.children).reduce((acc, child) =>
                acc + ((averages.avg_top - offset(child).top)**2), 0) / el.children.length);

        averages.avg_left = Array.from(el.children).reduce((acc, child) =>
                acc + (offset(child).left - position.left), 0) / el.children.length;
        averages.weighted_left = calculate_weighted_avg(el, (elem) =>
                offset(elem).left - position.left, 1).weighted_avg;
        averages.sd_left = Math.sqrt(Array.from(el.children).reduce((acc, child) =>
                acc + ((averages.avg_left - offset(child).left)**2), 0) / el.children.length);

        averages.avg_height = Array.from(el.children).reduce((acc, child) =>
                acc + (dimension(child).height - dimension(el).height), 0) / el.children.length;
        averages.weighted_height = calculate_weighted_avg(el, (elem) =>
                dimension(elem).height, 1).weighted_avg;
        averages.sd_height = Math.sqrt(Array.from(el.children).reduce((acc, child) =>
                acc + ((averages.avg_height - dimension(child).height)**2), 0) / el.children.length);

        averages.avg_width = Array.from(el.children).reduce((acc, child) =>
                acc + (dimension(child).width - dimension(el).width), 0) / el.children.length;
        averages.weighted_width = calculate_weighted_avg(el, (elem) =>
                dimension(elem).width, 1).weighted_avg;
        averages.sd_width = Math.sqrt(Array.from(el.children).reduce((acc, child) =>
                acc + ((averages.avg_width - dimension(child).width)**2), 0) / el.children.length);
    } else {
        averages.avg_top = -1;
        averages.weighted_top = -1;
        averages.sd_top = -1;
        averages.avg_left = -1;
        averages.weighted_left = -1;
        averages.sd_left = -1;
        averages.avg_height = -1;
        averages.weighted_height = -1;
        averages.sd_height = -1;
        averages.avg_width = -1;
        averages.weighted_width = -1;
        averages.sd_width = -1;
    }

    let body = document.body, html = document.documentElement;
    return {
        url: window.location.href,
        tagName: el.tagName,
        role: el.getAttribute('role'),
        top: position.top,
        left: position.left,
        height: dimension(el).height,
        width: dimension(el).width,
        childs_count: el.querySelectorAll('*').length,
        window_height: Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight),
        window_elements_count: document.querySelectorAll('*').length,
        className: el.className,
        parent_landmark: landmark_parent(el.parentElement),
        label: label_for(el),
        xpath: get_xpath(el),
        word_count: count_words(el),
        ...counter,
        ...averages
    };
};


var list = window.mutations_observed;
window.mutations_observed = [];
return [get_all_features(target), list.map((el) => get_all_features(el))];
        ''')

        print(f'Found {len(list_of_mutations[1])} mutations for {className}-{event}.')
        print(f'Writing mutations to {results_dir}/{domain}/mutations-{className}-{event}.json...')
        with open(f'./{results_dir}/{domain}/mutations-{className}-{event}.json', 'w') as f:
            f.write(str(list_of_mutations))

        print('\n')

driver.quit()


