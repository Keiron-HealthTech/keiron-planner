#!/usr/bin/env python3
"""El adapter de Linear. El contrato de las doce operaciones y de los códigos de
salida vive en scripts/LINEAR-OPERATIONS.md."""
import argparse
import sys

NO_IMPLEMENTADO = 9


def die(codigo, mensaje, remediacion):
    """El único terminador del archivo: el único sys.exit vive acá. El tercer
    argumento no lleva default, así que olvidarlo es un TypeError y no una omisión."""
    print("linear.py: %s\n  remediación: %s" % (mensaje, remediacion), file=sys.stderr)
    sys.exit(codigo)


def cmd_stub(args):
    die(NO_IMPLEMENTADO,
        "el subcomando %s todavía no está implementado" % args.operacion,
        "espera al corte que lo construye")


def construir_parser():
    parser = argparse.ArgumentParser(prog="linear.py")
    # required=True: sin él, un adapter invocado sin subcomando sale 1 o 0 en vez de 2.
    subs = parser.add_subparsers(dest="operacion", required=True)

    # Los doce se declaran explícitos, sin bucle: con un bucle el AST ve un solo
    # literal y las afirmaciones sobre el conjunto de subcomandos se vuelven vacuas.
    p_preflight = subs.add_parser("preflight")
    p_preflight.add_argument("--team", required=True)
    p_preflight.add_argument("--bootstrap", action="store_true")
    p_preflight.set_defaults(func=cmd_stub)

    p_map_create = subs.add_parser("map:create")
    p_map_create.add_argument("--ctx", required=True)
    p_map_create.set_defaults(func=cmd_stub)

    p_map_read = subs.add_parser("map:read")
    p_map_read.set_defaults(func=cmd_stub)

    p_map_write = subs.add_parser("map:write")
    p_map_write.set_defaults(func=cmd_stub)

    p_ticket_create = subs.add_parser("ticket:create")
    p_ticket_create.add_argument("--ctx", required=True)
    p_ticket_create.set_defaults(func=cmd_stub)

    p_ticket_block = subs.add_parser("ticket:block")
    p_ticket_block.set_defaults(func=cmd_stub)

    p_frontier_query = subs.add_parser("frontier:query")
    p_frontier_query.add_argument("--ctx", required=True)
    p_frontier_query.set_defaults(func=cmd_stub)

    p_ticket_claim = subs.add_parser("ticket:claim")
    p_ticket_claim.add_argument("--ctx", required=True)
    p_ticket_claim.set_defaults(func=cmd_stub)

    p_ticket_resolve = subs.add_parser("ticket:resolve")
    p_ticket_resolve.add_argument("--ctx", required=True)
    p_ticket_resolve.set_defaults(func=cmd_stub)

    p_ticket_rule_out = subs.add_parser("ticket:rule-out")
    p_ticket_rule_out.add_argument("--ctx", required=True)
    p_ticket_rule_out.set_defaults(func=cmd_stub)

    p_milestone_create = subs.add_parser("milestone:create")
    p_milestone_create.set_defaults(func=cmd_stub)

    p_work_write = subs.add_parser("work:write")
    p_work_write.add_argument("--ctx", required=True)
    p_work_write.set_defaults(func=cmd_stub)

    return parser


def main(argv):
    args = construir_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
