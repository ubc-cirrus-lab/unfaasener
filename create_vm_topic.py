from google.cloud import pubsub_v1


project_id = 'ubc-serverless-ghazal'
vm_topic_prefix = 'vmTopic'
vm_subscriber_prefix = 'vmSubscriber'


def list_vm_topic_indices(publisher):
    def parse_topic(topic):
        prefix = f'projects/{project_id}/topics/'
        if not topic.name.startswith(prefix):
            print('invalid topic name')
            return None
        return topic.name[len(prefix):]

    indices = set()
    for topic in publisher.list_topics(request={'project': f'projects/{project_id}'}):
        topic_name = parse_topic(topic)
        if topic_name and topic_name.startswith(vm_topic_prefix):
            index = int(topic_name[len(vm_topic_prefix):])
            indices.add(index)
    return indices


def list_vm_subscription_indices(subscriber):
    def parse_subscription(subscription):
        prefix = f'projects/{project_id}/subscriptions/'
        if not subscription.name.startswith(prefix):
            print('invalid subscription name')
            return None
        return subscription.name[len(prefix):]

    indices = set()
    for subscription in subscriber.list_subscriptions(request={'project': f'projects/{project_id}'}):
        sub_name = parse_subscription(subscription)
        if sub_name and sub_name.startswith(vm_subscriber_prefix):
            index = int(sub_name[len(vm_subscriber_prefix):])
            indices.add(index)
    return indices


def smallest_empty_index(publisher, subscriber):
    vm_topic_indices = list_vm_topic_indices(publisher)
    vm_subscription_indices = list_vm_subscription_indices(subscriber)

    indices = vm_topic_indices.union(vm_subscription_indices)

    cur = 0
    while True:
        if cur not in indices:
            return cur
        cur += 1


def create_vm_topic(publisher, topic_id):
    topic_path = publisher.topic_path(project_id, topic_id)
    print('Creating topic...')
    topic = publisher.create_topic(request={'name': topic_path})
    print(f'Created topic: {topic}')
    return topic_path


def create_subscriber(subscriber, subscription_id, topic_path):
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    with subscriber:
        print('Creating subscription...')
        subscription = subscriber.create_subscription(request={'name': subscription_path, 'topic': topic_path})
        print(f'Created subscription: {subscription}')


if __name__ == '__main__':
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    index = smallest_empty_index(publisher, subscriber)
    topic_path = create_vm_topic(publisher, f'{vm_topic_prefix}{index}')
    create_subscriber(subscriber, f'{vm_subscriber_prefix}{index}', topic_path)
