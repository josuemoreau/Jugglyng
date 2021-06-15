open Mlpost
open Box
open Command
open Point
open Num
open Path
open Helpers

let dot ~color ~name =
  Box.pic ~name
    (Path.fill ~color (Path.scale (Num.cm 0.3) fullcircle))

let bdot = dot ~color:Color.black

let rec foldi_desc f n b =
  if n = 0 then b
  else f n (foldi_desc f b (n - 1))

let rec foldi_asc f b n =
  if n = 0 then b
  else foldi_asc f (f b n) (n - 1)

let vd x = vec (dir x)

let emp_head_kind = Arrow.add_line Arrow.empty

let rec simple_juggling_seq dots max_time hpadding l =
  let t = ref (-1) in
  List.fold_left (fun acc h ->
      incr t;
      if !t < max_time then
        Arrow.point_to_point
          ~ind:(vd (-90.0))
          ~outd:(vd 90.0)
          ~sep:0.0
          ~style:jCurve
          ~kind:emp_head_kind
          (Box.ctr (Box.get ("bdot_" ^ string_of_int !t) dots))
          (if !t + h < max_time then
             (Box.ctr
                (Box.get ("bdot_" ^ (string_of_int (!t + h))) dots))
           else
             (Point.shift
                (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
                (cmp (2. *. hpadding *. float_of_int (!t + h - max_time + 1), 0.0)))
          ) :: acc
      else acc
    ) [] l

let fig1 =
  let max_time = 10 in
  let hpadding = 0.5 in
  let dots = Box.tabularl ~hpadding:(cm hpadding) [
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time;
      foldi_asc (fun l i ->
          Box.tex (string_of_int (i - 1)) :: l) [] max_time
    ] in
  seq ([
      Box.draw dots;
    ] @ simple_juggling_seq dots 10 hpadding [3; 3; 3; 3; 3; 3; 3])

let fig2 =
  let max_time = 10 in
  let hpadding = 0.5 in
  let dots = Box.tabularl ~hpadding:(cm hpadding) [
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time;
      foldi_asc (fun l i ->
          Box.tex (string_of_int (i - 1)) :: l) [] max_time
    ] in
  seq ([
      Box.draw dots;
    ] @ simple_juggling_seq dots 10 hpadding [4; 2; 0; 4; 2; 0; 4; 2; 0; 4])

let () =
  let figs = [fig1; fig2] in
  List.iteri (fun i x -> Metapost.emit ("figure-" ^ string_of_int i) x) figs
