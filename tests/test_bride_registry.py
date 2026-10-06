from bride.contracts import GOVERNING_QUESTION
from bride.registry import DONORS


def test_governing_question_is_exact():
    assert GOVERNING_QUESTION == (
        "Does changing this internal state predictably change what the same individual "
        "attends to, remembers, predicts, learns, decides, or does later, while preserving "
        "historical truth and architectural authority?"
    )


def test_registry_ids_unique():
    ids = [d.mechanism_id for d in DONORS]
    assert len(ids) == len(set(ids))


def test_all_behavioral_donors_name_target_channels():
    for donor in DONORS:
        if donor.role.value in {"mechanism", "historical"}:
            assert donor.target_channels
