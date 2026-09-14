package tools

import "testing"

// Minimal real-world nmap XML snippet.
const sampleNmapXML = `<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sV example.com">
  <host>
    <status state="up"/>
    <address addr="93.184.216.34" addrtype="ipv4"/>
    <hostnames>
      <hostname name="example.com" type="user"/>
    </hostnames>
    <ports>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="nginx" version="1.18.0"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https" product="nginx" version="1.18.0"/>
      </port>
      <port protocol="tcp" portid="22">
        <state state="closed"/>
        <service name="ssh"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 5.4" accuracy="95"/>
    </os>
  </host>
</nmaprun>`

func TestParseNmapXML_HappyPath(t *testing.T) {
	hosts, err := parseNmapXML(sampleNmapXML)
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if len(hosts) != 1 {
		t.Fatalf("want 1 host, got %d", len(hosts))
	}
	h := hosts[0]
	if h.Address != "93.184.216.34" {
		t.Errorf("address: %s", h.Address)
	}
	if len(h.Hostnames) != 1 || h.Hostnames[0] != "example.com" {
		t.Errorf("hostnames: %v", h.Hostnames)
	}
	if h.OS != "Linux 5.4" {
		t.Errorf("os: %s", h.OS)
	}
	// Closed port should be filtered.
	if len(h.Ports) != 2 {
		t.Fatalf("want 2 open ports, got %d", len(h.Ports))
	}
	p := h.Ports[0]
	if p.PortID != 80 || p.Service != "http" || p.Product != "nginx" || p.Version != "1.18.0" {
		t.Errorf("unexpected port detail: %+v", p)
	}
}

func TestParseNmapXML_DownHostsAreSkipped(t *testing.T) {
	xml := `<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="down"/>
    <address addr="1.1.1.1" addrtype="ipv4"/>
    <ports></ports>
  </host>
</nmaprun>`
	hosts, err := parseNmapXML(xml)
	if err != nil {
		t.Fatal(err)
	}
	if len(hosts) != 0 {
		t.Fatalf("down host should be filtered, got %d", len(hosts))
	}
}

func TestParseNmapXML_Malformed(t *testing.T) {
	if _, err := parseNmapXML("<not>even</xml>"); err == nil {
		// encoding/xml is lenient — it doesn't always error on this.
		// If it doesn't, at least verify we got nothing useful.
		hosts, _ := parseNmapXML("<not>even</xml>")
		if len(hosts) != 0 {
			t.Fatal("malformed xml should not produce hosts")
		}
	}
}
