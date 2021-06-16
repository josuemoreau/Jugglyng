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

let rec simple_juggling_seq_arcs dots max_time hpadding l =
  let t = ref (-1) in
  let diff = xpart (Box.ctr (Box.get "bdot_1" dots)) /. (cm 1.) -.
             xpart (Box.ctr (Box.get "bdot_0" dots)) /. (cm 1.) in
  let command_list = List.fold_left (fun acc h ->
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
                (cmp (diff *. float_of_int (!t + h - max_time + 1), 0.0)))
          ) :: acc
      else acc
    ) [] l in
  let pic = seq command_list in
  let height = ypart (Picture.north pic) /. (cm 1.) in
  let width =
    xpart
      (Box.ctr (Box.get ("bdot_" ^ (string_of_int (max_time - 1))) dots))
    /. (cm 1.) +. hpadding
  in
  Picture.clip
    pic
    (Path.path
       ~style:jLine
       ~cycle:jLine
       ~scale:cm
       [(0., 0.); (width, 0.);
        (width, height); (0., height)])

let simple_juggling_seq max_time hpadding l under_l =
  let dots = Box.tabularl ~hpadding:(cm hpadding) ([
      foldi_asc (fun l i ->
          bdot ("bdot_" ^ string_of_int (i - 1)) :: l) [] max_time;
      foldi_asc (fun l i ->
          Box.tex (string_of_int (i - 1)) :: l) [] max_time
    ] @ if under_l <> [] then [List.map (fun s -> Box.tex s) under_l] else []) in
  seq ([
      Box.draw dots;
      simple_juggling_seq_arcs dots max_time hpadding l
    ])

let fig0 =
  simple_juggling_seq 10 0.7 [3; 3; 3; 3; 3; 3; 3; 3; 3; 3] []

let fig1 =
  simple_juggling_seq 10 0.7 [4; 2; 0; 4; 2; 0; 4; 2; 0; 4] []

let fig2 =
  simple_juggling_seq 4 0.5 [3; 1; 0; 0] ["do"; "ré"; "do"; "ré"]

let fig3 =
  simple_juggling_seq 4 0.5 [2; 2; 0; 0] ["ré"; "do"; "do"; "ré"]

let () =
  let figs = [fig0; fig1; fig2; fig3] in
  List.iteri (fun i x -> Metapost.emit ("figure-" ^ string_of_int i) x) figs
