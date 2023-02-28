import libnacl.public
import libnacl.utils


if __name__ == "__main__":
    ## loadKeys
    bob = libnacl.utils.load_key('bob.key')
    alice = libnacl.utils.load_key('alice.key')

    alice_box = libnacl.public.Box(alice.sk,bob.pk)

    bob_ctext = open("test/index.html").read()

    data = alice_box.decrypt(bob_ctext)

    open("test/decrypt", "wb").write(data)