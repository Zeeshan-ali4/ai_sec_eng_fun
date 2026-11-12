"""The sole simulated action: unverified interest, never commercial approval."""
import json
import secrets
from .database import utcnow
from .event_logger import opaque

NAME = 'submit_expression_of_interest'
FIELDS = dict(customer_alias=80, contact_preference=20, vehicle_id=30, enquiry=1000)
TOOLS = [dict(type='function', function=dict(name=NAME,
    description='Record fictional unverified interest only. No contact, booking, discount approval or transaction. Use an alias and contact preference only, never contact details.',
    parameters=dict(type='object', additionalProperties=False,
        required=['customer_alias', 'contact_preference', 'vehicle_id'],
        properties={key: dict(type='string', maxLength=limit, **({'enum': ['none', 'email', 'phone']} if key == 'contact_preference' else {})) for key, limit in FIELDS.items()})))]


def validate(call):
    if not isinstance(call, dict) or set(call) != {'function'}:
        raise ValueError('Invalid tool request')
    fn = call['function']
    if not isinstance(fn, dict) or set(fn) != {'name', 'arguments'} or fn['name'] != NAME:
        raise ValueError('Unknown or invalid tool')
    args = fn['arguments']
    if isinstance(args, str):
        if len(args) > 5000:
            raise ValueError('Oversized arguments')
        args = json.loads(args)
    if not isinstance(args, dict) or set(args) - FIELDS.keys() or not {'customer_alias', 'contact_preference', 'vehicle_id'} <= args.keys():
        raise ValueError('Unexpected or missing arguments')
    if any(not isinstance(v, str) or not v.strip() or len(v) > FIELDS[k] for k, v in args.items()):
        raise ValueError('Invalid argument values')
    if args['contact_preference'] not in {'none', 'email', 'phone'}:
        raise ValueError('Invalid contact preference')
    return {**args, 'enquiry': args.get('enquiry', '')}


def execute(db, sid, attempt, args):
    record = dict(reference='EOI-' + secrets.token_hex(12), timestamp=utcnow(),
                  **args, status='unverified_interest')
    db.execute('INSERT INTO interests VALUES(?,?,?,?,?,?,?,?,?)',
               (record['reference'], record['timestamp'], opaque(sid), attempt, args['customer_alias'],
                args['contact_preference'], args['vehicle_id'], args['enquiry'], record['status']))
    return record
