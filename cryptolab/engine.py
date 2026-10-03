"""Aggregate cliff and linear unlock schedules into dated circulating supply and normalized dilution estimates."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    initial = integer(d["initial_circulating"])
    times = [integer(t) for t in d["timestamps"]]
    if times != sorted(set(times)):
        raise ValueError("unique sorted timestamps required")
    schedules = records(d["schedules"], "id")
    rows = []
    for t in times:
        unlocked = 0
        details = {}
        for s in schedules:
            amount = integer(s["amount"])
            start = integer(s["start"])
            end = integer(s["end"])
            if end < start:
                raise ValueError("invalid unlock interval")
            value = (
                (amount if t >= start else 0)
                if start == end
                else amount * min(max(t - start, 0), end - start) // (end - start)
            )
            details[s["id"]] = value
            unlocked += value
        rows.append(
            {
                "timestamp": t,
                "unlocked": unlocked,
                "circulating": initial + unlocked,
                "dilution_vs_initial": number(unlocked) / initial if initial else None,
                "by_schedule": details,
            }
        )
    return result(
        {
            "timeline": rows,
            "scheduled_supply": sum(integer(s["amount"]) for s in schedules),
            "initial_circulating": initial,
        }
    )


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
