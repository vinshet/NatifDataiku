<head>
  <meta charset="UTF-8">
</head>
<style>
      .text-center {
        font-size: 14pt;
        line-height: 2;
      }
	  .progress-label {
    position: absolute;
    left: 50%;
    padding-top: 8px;
    font-weight: bold;
    text-shadow: 1px 1px 0 #fff;
}

	.picture{

	}
</style>

<link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">
  <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
  <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
<?php
$conn = mysqli_connect("192.168.100.168", "padmin", "natif.ai19#", "natif_annotator");
$conn->set_charset("utf8");
function getDir($filename)
{
	return substr($filename,0,1).'/'.substr($filename,1,1).'/'.substr($filename,2,1);
}
if($_POST["snippetsnb"])
{
	$snippetsnb=$_POST["snippetsnb"];
}else
{
	$snippetsnb=10;
}
if($_POST["action"])
{
	$idlist=explode(',',$_POST["snippets_update"]);
	foreach($idlist as $id)
	{
		if($_POST[$id."_typo"]=="" && $_POST[$id."_readable"]=="0")
		{
			//return none treated snippet to original state
			$sql="UPDATE line_snippets SET status=1 WHERE id IN(".$id.")";
			$conn->query($sql);
		}
		else
		{
		    if($_POST[$id."_readable"]=="0")
		    {
		    	$typo = mysqli_real_escape_string($conn, $_POST[$id."_typo"]);
                $sql='UPDATE line_snippets SET status=3, text="'.$typo.'"';
                $sql.=" WHERE id IN(".$id.")";
                $conn->query($sql);
		    }else
		    {
		    	$typo = mysqli_real_escape_string($conn, $_POST[$id."_typo"]);
                $sql='UPDATE line_snippets SET status=4';
                $sql.=" WHERE id IN(".$id.")";
                $conn->query($sql);
		    }

		}
	}
}

$sql="SELECT * from line_snippets WHERE status=1 OR (status=2 AND dom < (NOW() - INTERVAL 1 DAY)) Order by id ASC LIMIT $snippetsnb";

?>

<form method="POST" accept-charset="UTF-8">
Default Snippets number <input type="text" id="snippetsnb" name="snippetsnb" value="<?php echo $snippetsnb ?>"/>
<?php
if ($res=$conn->query($sql)) {
	echo '<table border="1">';
	echo '<tr><td>Snippet</td><td>Typo</td><td>Readability</td></tr>';
	 while ($row = $res->fetch_array()) {
        echo '<tr><td><img src="'.getDir($row["snippet_id"]).'/'.$row["snippet_id"].'/'.$row["snippet_id"].'.jpg" class="picture" /></td><td><input type="text" name="'.$row["id"].'_typo" value="'.$row["text"].'" /></td><td><input type="radio" name="'.$row["id"].'_readable" value="0" checked> Ok <br /><input type="radio" name="'.$row["id"].'_readable" value="2" > Not Ok </td></tr>';
		$update_busy[]=$row["id"];
    }
	echo '<input type="hidden" name="snippets_update" value="'.implode(',',$update_busy).'" />';
	$sql="UPDATE line_snippets SET status=2,dom=now() WHERE id IN(".implode(',',$update_busy).")";
	$conn->query($sql);
	echo '</table>';
}

?>
<button type="submit" value="next" name="action">
NEXT
</button>
</form>