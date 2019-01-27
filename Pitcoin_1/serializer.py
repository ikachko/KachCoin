class Serializer:
    @staticmethod
    def serialize(num_of_coins, sender_addr, recipient_addr, sender_public_key, signature):
        return (
            '%04x' % num_of_coins +
            sender_addr +
            recipient_addr +
            sender_public_key +
            signature
        )


class Deserializer:
    @staticmethod
    def deserialize(transaction):
        num_of_coins = int(transaction[0:4], 16)
        send_addr = transaction[4:38]
        recipient_addr = transaction[38:72]
        pub_key = transaction[72:202]
        signature = transaction[202:]
        return dict({
            'num_of_coins' : num_of_coins,
            'sender_addr' : send_addr,
            'recepient_addr' : recipient_addr,
            'public_key' : pub_key,
            'signature' : signature
                    })