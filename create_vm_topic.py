from google.cloud import pubsub_v1


project_id = 'ubc-serverless-ghazal'
vm_topic_prefix = 'vmTopic'


def parse_topic(topic):
    prefix = f'projects/{project_id}/topics/'
    if not topic.name.startswith(prefix):
        print('invalid topic name')
        return None
    return topic.name[len(prefix):]


def smallest_empty_index(publisher):
    project_path = f'projects/{project_id}'
    vm_topic_indices = set()

    for topic in publisher.list_topics(request={'project': project_path}):
        topic_name = parse_topic(topic)
        if topic_name and topic_name.startswith(vm_topic_prefix):
            index = int(topic_name[len(vm_topic_prefix):])
            vm_topic_indices.add(index)

    cur = 0
    while True:
        if cur not in vm_topic_indices:
            return cur
        cur += 1


def create_vm_topic(publisher, topic_id):
    topic_path = publisher.topic_path(project_id, topic_id)
    print('Creating topic...')
    topic = publisher.create_topic(request={'name': topic_path})
    print(f'Created topic: {topic}')


if __name__ == '__main__':
    publisher = pubsub_v1.PublisherClient()
    index = smallest_empty_index(publisher)
    create_vm_topic(publisher, f'{vm_topic_prefix}{index}')
