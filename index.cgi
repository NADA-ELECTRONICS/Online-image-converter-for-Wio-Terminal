#!/usr/bin/perl
#
# Online-image-converter-for-Wio-Terminal
# BMP(24bit) to RGB332/RGB565
# Copyright (c) 2020 Takehiro Yamaguchi
# This software is released under the MIT License.
# http://opensource.org/licenses/mit-license.php
#

use strict;
use Archive::Zip qw/:ERROR_CODES/;
use CGI;
use utf8;


# Query
my $query = new CGI;
my $rgb = $query->param('rgb');
my $filename = $query->param('upload_file');
if ($filename eq '') {
	# Text Output
	print $query->header;
	print $query->start_html(-title=>'Online image converter for Wio Terminal');
	print '<h1>Online image converter for Wio Terminal</h1>';
	print '<a href="https://wiki.seeedstudio.com/Wio-Terminal-LCD-Loading-Image/" target="blank">https://wiki.seeedstudio.com/Wio-Terminal-LCD-Loading-Image/</a>';
	print '<p>Windows BMP(24bit 320x240) to RGB332|565</p>';
	print '<form action="index.cgi" enctype="multipart/form-data" method="POST">';
	print '<label for="uppic">Choose file to upload </label><input type="file" id="uppic" name="upload_file" size="32" accept=".bmp"/><br />';
	print '<input type="radio" name="rgb" value="332">RGB332';
	print '<input type="radio" name="rgb" value="565" checked>RGB565<br />';
	print '<input type="submit" value="Convert and Download(zip)" />';
	print '</form>';
	print '<p><a href="https://twitter.com/nada_tokki" target="blank">Twitter @nada_tokki</a></p>';
	print $query->end_html;
	exit;
}


# Get file
my (@file, $val);
while(read($filename, $val, 1)) {
	$val = sprintf("%02X", unpack("C",$val));
	push(@file, $val);
}


# Check image data
my $minetype = $query->uploadInfo($filename)->{'Content-Type'};
if ($minetype ne "image/bmp") {
	&Html_output("Err", "Error : MINE type"); exit;
}
if ($file[20] ne "00" || $file[21] ne "00") {
	&Html_output("Err", "Error : width"); exit;
}
if ($file[24] ne "00" || $file[25] ne "00") {
	&Html_output("Err", "Error : height"); exit;
}
if ($file[28] ne "18" || $file[29] ne "00") {
	&Html_output("Err", "Error : color depth"); exit;
}
if ($file[12] ne "00" || $file[13] ne "00") {
	&Html_output("Err", "Error : offset"); exit;
}


# Get offset
my $offset = hex($file[10]);
$offset += (hex($file[11]) * 256);

# Get image size
my $imgWidth = hex($file[18]);
$imgWidth += (hex($file[19]) * 256);
my $imgHeight = hex($file[22]);
$imgHeight += (hex($file[23]) * 256);


# Convert RGB

my $fileRGB332 = pack("C", hex($file[18])) . pack("C", hex($file[19])) . pack("C", hex($file[22])) . pack("C", hex($file[23]));
my $fileRGB565 = $fileRGB332;

my $point = $#file + 1;

for (my $y = 0; $y < $imgHeight; $y ++) {
	$point -= $imgWidth * 3;
	for (my $x = 0; $x < $imgWidth; $x ++) {
		my ($b, $g, $r) = (hex($file[$x * 3 + $point]), hex($file[$x * 3 + 1 + $point]), hex($file[$x * 3 + 2 + $point]));
		if ($rgb eq "332") {
			my $val332 = &ConvertToRGB332($b, $g, $r);
			$fileRGB332 .= $val332
		}
		elsif ($rgb eq "565") {
			$fileRGB565 .= &ConvertToRGB565($b, $g, $r);
		}
	}
}

# Zip
if ($rgb eq "332") {
	&ZIPtoHTTP($fileRGB332, "rgb332.bmp");
}
elsif ($rgb eq "565") {
	&ZIPtoHTTP($fileRGB565, "rgb565.bmp");
}


&Html_output("Err", "Error");
exit;


sub ZIPtoHTTP {
	my $zip = Archive::Zip->new;
	$zip->addString($_[0], $_[1])->desiredCompressionMethod(Archive::Zip::COMPRESSION_DEFLATED);
	my $stdout = IO::File->new->fdopen(fileno(STDOUT), "w") || croak($!);
	$stdout->printflush("Content-Type: application/zip\n");
	$stdout->printflush("Content-Disposition: filename=rgb$rgb.zip\n");
	$stdout->printflush("Pragma: no-cache\n\n");
	$zip->writeToFileHandle($stdout, 0);
	$stdout->close;
}


sub Html_output {
	print $query->header;
	print $query->start_html(-title=>"$_[0]");
	print "$_[1]";
	print $query->end_html;
}


sub ConvertToRGB332 {
	my $r3 = $_[2] >> 5;
	my $g3 = $_[1] >> 5;
	my $b2 = $_[0] >> 6;
	my $rgb332 = ($r3 << 5) | ($g3 << 2) | $b2;
	my $v = pack("C", $rgb332);
	return $v;
}


sub ConvertToRGB565 {
	my $r5 = $_[2] >> 3;
	my $g6 = $_[1] >> 2;
	my $b5 = $_[0] >> 3;
	my $rgb565 = ($r5 << 11) | ($g6 << 5) | $b5;
	my $v = pack("n", $rgb565);
	return $v;
}


