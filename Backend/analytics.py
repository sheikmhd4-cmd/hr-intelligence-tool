from backend.database import CandidateResult


def get_top_candidates(db, limit=10):
    return (
        db.query(CandidateResult)
        .order_by(CandidateResult.total_score.desc())
        .limit(limit)
        .all()
    )


def get_all_results(db):
    return db.query(CandidateResult).all()


def clear_all_results(db):
    db.query(CandidateResult).delete()
    db.commit()
