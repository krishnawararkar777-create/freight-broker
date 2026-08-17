import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from db.session import Base
from scripts.seed_demo_data import seed_data

def test_seed_demo_data_idempotency():
    """Running seed_demo_data twice must not duplicate rows."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        # Run 1
        counts_run_1 = seed_data(db)
        assert counts_run_1["organizations"] == 1, "First run should seed org"
        assert counts_run_1["users"] == 1, "First run should seed user"
        assert counts_run_1["carriers"] == 3, "First run should seed 3 carriers"
        assert counts_run_1["claims"] == 1, "First run should seed 1 primary claim"

        # Run 2 (Idempotency test)
        counts_run_2 = seed_data(db)
        assert counts_run_2["organizations"] == 0, "Second seed run created duplicate org"
        assert counts_run_2["users"] == 0, "Second seed run created duplicate user"
        assert counts_run_2["carriers"] == 0, "Second seed run created duplicate carriers"
        assert counts_run_2["claims"] == 0, "Second seed run created duplicate claims"
    finally:
        db.close()
