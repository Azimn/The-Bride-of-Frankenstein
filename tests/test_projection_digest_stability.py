from frankenstein.cartridge import CharacterOrigin
from frankenstein.engine import FrankensteinEngine


def test_projection_digest_ignores_sqlite_row_order(tmp_path):
    subject = FrankensteinEngine(
        tmp_path / "subject",
        CharacterOrigin(
            entity_id="projection-order-subject",
            display_name="Ada",
        ),
    )
    event = subject.update_relationship(
        "jay",
        {
            "trust": 0.35,
            "familiarity": 0.25,
            "attachment": 0.10,
        },
    )

    before = subject.store.projection_digest()

    with subject.store.transaction() as conn:
        row = conn.execute(
            "SELECT actor_id,dimension,value,source_event_id "
            "FROM relationships "
            "WHERE actor_id='jay' AND dimension='trust'"
        ).fetchone()
        conn.execute(
            "DELETE FROM relationships "
            "WHERE actor_id='jay' AND dimension='trust'"
        )
        conn.execute(
            "INSERT INTO relationships(actor_id,dimension,value,source_event_id) "
            "VALUES(?,?,?,?)",
            (
                row["actor_id"],
                row["dimension"],
                row["value"],
                row["source_event_id"],
            ),
        )

    after = subject.store.projection_digest()

    assert before == after
    assert subject.store.verify_integrity().ok
    assert event.event_id
