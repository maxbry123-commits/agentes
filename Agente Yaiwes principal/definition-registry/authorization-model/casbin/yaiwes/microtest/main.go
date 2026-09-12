package main
import("encoding/json";"fmt";"os";casbin "github.com/casbin/casbin/v3";"github.com/casbin/casbin/v3/model")
func main(){
  text:=`[request_definition]
r = sub, obj, act
[policy_definition]
p = sub, obj, act
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = r.sub == p.sub && r.obj == p.obj && r.act == p.act`
  m,err:=model.NewModelFromString(text);if err!=nil{panic(err)};e,err:=casbin.NewEnforcer(m);if err!=nil{panic(err)}
  if ok,err:=e.AddPolicy("alice","data1","read");err!=nil||!ok{panic(fmt.Sprintf("alice:%v:%v",ok,err))};if ok,err:=e.AddPolicy("bob","data2","write");err!=nil||!ok{panic(fmt.Sprintf("bob:%v:%v",ok,err))}
  ar,err:=e.Enforce("alice","data1","read");if err!=nil{panic(err)};aw,err:=e.Enforce("alice","data1","write");if err!=nil{panic(err)};bw,err:=e.Enforce("bob","data2","write");if err!=nil{panic(err)};if !ar||aw||!bw{panic("ACL_FAIL")}
  r:=map[string]interface{}{"status":"PASS","alice_data1_read":ar,"alice_data1_write":aw,"bob_data2_write":bw};b,_:=json.Marshal(r);fmt.Println("YAIWES_CASBIN_RESULT="+string(b));if err:=os.WriteFile("yaiwes/microtest-result.json",append(b,'\n'),0644);err!=nil{panic(err)}
}
