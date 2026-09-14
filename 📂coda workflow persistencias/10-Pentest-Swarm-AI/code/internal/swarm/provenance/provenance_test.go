package provenance

import (
	"testing"
	"time"
)

func TestSignAndVerify_Roundtrip(t *testing.T) {
	s, err := NewSigner()
	if err != nil {
		t.Fatalf("NewSigner: %v", err)
	}
	now := time.Now().Unix()
	sig := s.Sign("camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"port":443}`), now)
	if err := Verify(s.PublicKey(), sig, "camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"port":443}`), now); err != nil {
		t.Errorf("verify roundtrip: %v", err)
	}
}

func TestVerify_DetectsTamper(t *testing.T) {
	s, _ := NewSigner()
	now := time.Now().Unix()
	sig := s.Sign("camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"port":443}`), now)

	// Same key + sig, but data was swapped — must fail.
	err := Verify(s.PublicKey(), sig, "camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"port":22}`), now)
	if err == nil {
		t.Error("verify should fail when data is tampered")
	}
}

func TestVerify_DetectsAgentImpersonation(t *testing.T) {
	// An attacker uses their own key but tries to write under "recon"'s name.
	attacker, _ := NewSigner()
	legit, _ := NewSigner()
	now := time.Now().Unix()
	// Attacker signs a finding claiming to be from recon.
	sig := attacker.Sign("camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"fake":true}`), now)
	// Verifier uses recon's REAL public key — verification must fail.
	err := Verify(legit.PublicKey(), sig, "camp-1", "recon", "PORT_OPEN", "example.com", []byte(`{"fake":true}`), now)
	if err == nil {
		t.Error("verify should fail when sig was made by a different keypair")
	}
}

func TestVerify_RejectsMalformedKeyAndSig(t *testing.T) {
	if err := Verify(nil, nil, "", "", "", "", nil, 0); err == nil {
		t.Error("verify should fail on empty key/sig")
	}
	if err := Verify(make([]byte, 16), make([]byte, 64), "", "", "", "", nil, 0); err == nil {
		t.Error("verify should fail on wrong-length key")
	}
}
