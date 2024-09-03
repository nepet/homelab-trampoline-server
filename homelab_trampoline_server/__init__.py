from pyln.client import Plugin
from pyln.proto.primitives import varint_decode
from binascii import unhexlify
from io import BytesIO
import random
import time

INVOICE_TYPE = 33001
AMOUNT_TYPE = 33003

plugin = Plugin(
    dynamic=False,
    init_features=1 << 427,
)


@plugin.hook("htlc_accepted")
def on_htlc_accepted(htlc, onion, plugin, **kwargs):
    plugin.log(f"got onion {onion}")
    payment_metadata = unhexlify(onion["payment_metadata"])
    payment_metadata = BytesIO(payment_metadata)

    try:
        invoice_type = varint_decode(payment_metadata)
        assert invoice_type == INVOICE_TYPE

        invoice_length = varint_decode(payment_metadata)
        plugin.log(
            f"reading {invoice_length} bytes from payment metadata for {invoice_type} as the invoice"
        )
        invoice_value = payment_metadata.read(invoice_length).decode('utf-8')
    except Exception as e:
        plugin.log(f"no trampoline payment detected {e}")
        return {"result": "continue"}

    try:
        amount_type = varint_decode(payment_metadata)
        assert amount_type == AMOUNT_TYPE

        amount_length = varint_decode(payment_metadata)
        plugin.log(
            f"reading {amount_length} bytes from payment metadata for {amount_type} as the amount"
        )
        amount_value = payment_metadata.read(amount_length)
        amount_msat_value = int.from_bytes(amount_value, 'big')
    except Exception as e:
        plugin.log(f"got error on htlc_accepted {e}")
        return {"result": "fail", "failure_message": "2002"}

    try:
        duration = random.randint(30,90)
        plugin.log(f"sleep for {duration} sec before continuing")
        time.sleep(duration)

        label = f"trampoline-{random.randint(1,65535)}"
        plugin.log(f"attempting pay for invoice={invoice_value} and label={label}")
        res = plugin.rpc.pay(invoice_value, label=label)
        plugin.log("pay response is {res}")
        return {
            "result": "resolve",
            "payment_key": res["payment_preimage"],
        }
    except Exception as e:
        plugin.log(f"got error trying to pay invoice {invoice_value} {e}")
        return {"result": "fail", "failure_message": "2002"}


def run():
    plugin.run()
