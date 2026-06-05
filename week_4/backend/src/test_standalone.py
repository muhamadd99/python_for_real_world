"""
STANDALONE TEST - No External Dependencies
Malaysian Bank Receipt OCR Extraction System

This test requires ONLY the core receipt_extractor_v2.py file
No network calls, no external tools needed
"""

from receipt_extractor_v2 import extract_receipt

def test_basic():
    """Most basic test - single bank"""
    receipt = "MAYBANK\nBeneficiary Name: ABC Company\nAmount: RM100.00"
    result = extract_receipt(receipt)
    assert result.recipient_name == "ABC Company", f"Expected 'ABC Company', got '{result.recipient_name}'"
    assert result.amount == "RM100.00", f"Expected 'RM100.00', got '{result.amount}'"
    print("[PASS] Basic extraction")

def test_all_banks():
    """Test all 5 major banks"""
    tests = [
        ("Maybank", "MAYBANK\nBeneficiary Name: Company A\nAmount: RM100.00", "Company A"),
        ("RHB", "RHB\nTo: Company B\nAmount: RM200.00", "Company B"),
        ("BSN", "BSN\nTransfer To: Company C\nAmount: RM300.00", "Company C"),
        ("CIMB", "CIMB\nRecipient: Company D\nAmount: RM400.00", "Company D"),
        ("PUBLIC BANK", "PUBLIC BANK\nBeneficiary: Company E\nAmount: RM500.00", "Company E"),
    ]
    
    for bank_name, receipt, expected in tests:
        result = extract_receipt(receipt)
        assert result.recipient_name == expected, f"{bank_name} failed: got {result.recipient_name}"
        print(f"[PASS] {bank_name}")

def test_ocr_errors():
    """Test OCR error tolerance"""
    # Spelling errors
    receipt = "MAYBANK\nBenificiary Name: Test Company\nAmmount: RM100.00"
    result = extract_receipt(receipt)
    assert result.recipient_name is not None, "Failed to extract with spelling errors"
    print("[PASS] OCR spelling errors")

def test_batch():
    """Test batch processing"""
    receipts = [
        "MAYBANK\nBeneficiary Name: A\nAmount: RM100",
        "RHB\nTo: B\nAmount: RM200",
        "CIMB\nRecipient: C\nAmount: RM300",
    ]
    
    results = [extract_receipt(r) for r in receipts]
    assert len(results) == 3, "Batch processing failed"
    assert all(r.recipient_name for r in results), "Some receipts not extracted"
    print("[PASS] Batch processing")

def test_confidence():
    """Test confidence scoring"""
    # Complete receipt
    receipt = "MAYBANK\nBeneficiary Name: ABC\nAmount: RM100\nDate: 2026-06-05"
    result = extract_receipt(receipt)
    assert result.confidence > 0.75, f"Low confidence: {result.confidence}"
    print("[PASS] Confidence scoring")

def test_json_output():
    """Test JSON compatibility"""
    import json
    receipt = "MAYBANK\nBeneficiary Name: ABC\nAmount: RM100"
    result = extract_receipt(receipt)
    
    data = {
        "recipient": result.recipient_name,
        "amount": result.amount,
        "bank": result.detected_bank.value,
    }
    
    json_str = json.dumps(data)
    assert json_str, "JSON serialization failed"
    print("[PASS] JSON output")

def test_empty_handling():
    """Test error handling"""
    result = extract_receipt("")
    assert result is not None, "Failed to handle empty receipt"
    print("[PASS] Empty receipt handling")

if __name__ == "__main__":
    print("=" * 60)
    print("STANDALONE TESTS")
    print("No network calls, no external dependencies")
    print("=" * 60)
    print()
    
    try:
        test_basic()
        test_all_banks()
        test_ocr_errors()
        test_batch()
        test_confidence()
        test_json_output()
        test_empty_handling()
        
        print()
        print("=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("System is working correctly.")
        print("No 'failed to fetch' errors - everything is local.")
        
    except AssertionError as e:
        print(f"\n[FAIL] {str(e)}")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        exit(1)
