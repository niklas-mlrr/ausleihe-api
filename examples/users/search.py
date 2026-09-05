"""
IServ-Nutzer suchen oder alle abrufen.

Verwendung:
  python3 -m examples.users.search                     # alle Nutzer
  python3 -m examples.users.search <nachname>
  python3 -m examples.users.search Müller
  python3 -m examples.users.search --firstname <vorname>
  python3 -m examples.users.search --firstname Anna
"""
import sys

from examples._common import make_client

args = sys.argv[1:]
lastname = ""
firstname = ""

if args and args[0] == "--firstname":
    firstname = args[1] if len(args) > 1 else ""
elif args:
    lastname = args[0]

client = make_client()
users = client.users.search_by_name(lastname=lastname, firstname=firstname)

label = f"'{lastname or firstname}'" if (lastname or firstname) else "alle"
print(f"{len(users)} Nutzer ({label}):")
for u in users[:30]:
    act = u.get("act", u.get("username", "-"))
    fn = u.get("firstname", "")
    ln = u.get("lastname", "")
    print(f"  {act:<30} {fn} {ln}")

if len(users) > 30:
    print(f"  ... und {len(users) - 30} weitere.")
