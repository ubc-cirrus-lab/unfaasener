import argparse

from google.cloud import pubsub_v1


def list_vm_topic_indices(publisher, args):
    def parse_topic(topic):
        prefix = f'projects/{args.project_id}/topics/'
        if not topic.name.startswith(prefix):
            print('invalid topic name')
            return None
        return topic.name[len(prefix):]

    indices = set()
    for topic in publisher.list_topics(request={'project': f'projects/{args.project_id}'}):
        topic_name = parse_topic(topic)
        if topic_name and topic_name.startswith(args.vm_topic_prefix):
            index = int(topic_name[len(args.vm_topic_prefix):])
            indices.add(index)
    return indices


def list_vm_subscription_indices(subscriber, args):
    def parse_subscription(subscription):
        prefix = f'projects/{args.project_id}/subscriptions/'
        if not subscription.name.startswith(prefix):
            print('invalid subscription name')
            return None
        return subscription.name[len(prefix):]

    indices = set()
    for subscription in subscriber.list_subscriptions(request={'project': f'projects/{args.project_id}'}):
        sub_name = parse_subscription(subscription)
        if sub_name and sub_name.startswith(args.vm_subscriber_prefix):
            index = int(sub_name[len(args.vm_subscriber_prefix):])
            indices.add(index)
    return indices


def smallest_empty_index(publisher, subscriber, args):
    vm_topic_indices = list_vm_topic_indices(publisher, args)
    vm_subscription_indices = list_vm_subscription_indices(subscriber, args)

    indices = vm_topic_indices.union(vm_subscription_indices)

    cur = 0
    while True:
        if cur not in indices:
            return cur
        cur += 1


def create_vm_topic(publisher, topic_id, args):
    topic_path = publisher.topic_path(args.project_id, topic_id)
    print('Creating topic...')
    topic = publisher.create_topic(request={'name': topic_path})
    print(f'Created topic: {topic}')
    return topic_path


def delete_vm_topic(publisher, topic_id, args):
    topic_path = publisher.topic_path(args.project_id, topic_id)
    print('Deleting topic...')
    publisher.delete_topic(request={'topic': topic_path})
    print(f'Deleted topic: {topic_path}')


def create_subscriber(subscriber, subscription_id, topic_path, args):
    subscription_path = subscriber.subscription_path(args.project_id, subscription_id)
    with subscriber:
        print('Creating subscription...')
        subscription = subscriber.create_subscription(request={'name': subscription_path, 'topic': topic_path})
        print(f'Created subscription: {subscription}')


def delete_subscriber(subscriber, subscription_id, args):
    subscription_path = subscriber.subscription_path(args.project_id, subscription_id)
    with subscriber:
        print('Deleting subscription...')
        subscriber.delete_subscription(request={'subscription': subscription_path})
        print(f'Deleted subscription: {subscription_path}')


def check_args(args):
    if not args.create and not args.delete:
        print('Specify either --create or --delete flag to indicate mode.')
        exit(1)
    if args.create and args.delete:
        print('Specify either --create or --delete flag to indicate mode.')
        exit(1)
    if args.delete and args.index is None:
        print('Specify --index value to indicate which VM topic & subscriber to delete')
        exit(1)
    if args.create and args.index is not None:
        print('Do not specify --index value when creating VM topic & subscriber')
        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates VM topic and subscriber.')
    parser.add_argument('--create', action='store_true', help='Create VM topic and subscriber')
    parser.add_argument('--delete', action='store_true', help='Create VM topic and subscriber')
    parser.add_argument('--project_id', type=str, required=True, help='GCP project id')
    parser.add_argument('--vm_topic_prefix', type=str, default='vmTopic', help='Topic prefix')
    parser.add_argument('--vm_subscriber_prefix', type=str, default='vmSubscriber', help='Subscriber prefix')
    parser.add_argument('--index', type=int, help='"index" of VM topic/subscriber to delete. ex) 3 if VM topic is vmTopic3.')
    args = parser.parse_args()
    check_args(args)

    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    if args.create:
        index = smallest_empty_index(publisher, subscriber, args)
        topic_path = create_vm_topic(publisher, f'{args.vm_topic_prefix}{index}', args)
        create_subscriber(subscriber, f'{args.vm_subscriber_prefix}{index}', topic_path, args)
    elif args.delete:
        delete_vm_topic(publisher, f'{args.vm_topic_prefix}{args.index}', args)
        delete_subscriber(subscriber, f'{args.vm_subscriber_prefix}{args.index}', args)
