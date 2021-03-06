# vim: ts=4:sw=4:et:sta
from glob import glob
import logging
import math
import os
import re
import ROOT as r
import sys

r.gROOT.SetBatch()
r.gSystem.Load("libTTHTauTauRoast")

try:
    from ROOT import roast
except:
    sys.stderr.write("Failed to import 'roast'!\n")
    sys.exit(1)

from TTHTauTau.Roast.helper import *

def get_bkg_stack(histname, processes):
    res = r.THStack(histname + "_stack", histname + "_stack")

    for p in reversed(processes):
        h = p.GetHContainer()[histname].GetHisto()
        h.SetFillStyle(1001)
        h.SetFillColor(p.GetColor())
        h.SetLineColor(p.GetColor())
        h.SetLineWidth(0)
        res.Add(h)

    return res

def get_bkg_sum(histname, processes):
    res = None

    for p in processes:
        if not p.IsBackground():
            continue

        if not res:
            res = roast.HWrapper(p.GetHContainer()[histname])
        else:
            res.Add(p.GetHContainer()[histname])

    return res

def get_integrals(histname, processes):
    vals = []
    for p in processes:
        if p.GetHContainer()[histname].GetHisto():
            vals.append(p.GetHContainer()[histname].GetHisto().Integral())
    return vals

def get_maximum(histname, processes, inc_error=False):
    vals = []
    for p in processes:
        if inc_error:
            vals.append(p.GetHContainer()[histname].GetMaximumWithError())
        else:
            vals.append(p.GetHContainer()[histname].GetMaximum())
    return max(vals)

class SysErrors:
    def __init__(self, config):
        upfilenames = glob(config['paths']['systematics input'].format(s="*Up"))
        downfilenames = glob(config['paths']['systematics input'].format(s="*Down"))

        candidates = filter(lambda s: s != "Collisions", config['analysis']['plot'])

        self.__up = []
        for fn in upfilenames:
            logging.info("loading systematic shifts from %s", fn)
            procs = load("Roast", fn)
            normalize_processes(config, procs)
            combine_processes(config, procs)
            procs = map(lambda n: get_process(n, procs), candidates)
            self.__up.append((fn, procs))

        self.__down = []
        for fn in downfilenames:
            logging.info("loading systematic shifts from %s", fn)
            procs = load("Roast", fn)
            normalize_processes(config, procs)
            combine_processes(config, procs)
            procs = get_backgrounds(map(lambda n: get_process(n, procs), candidates))
            self.__down.append((fn, procs))

    def get_squared_bkg_shifts(self, procs, histname, histo):
        res = [0] * histo.GetHisto().GetNbinsX()
        for (fn, ps) in procs:
            bkg_sum = get_bkg_sum(histname, ps)

            for i in range(histo.GetHisto().GetNbinsX()):
                res[i] += (bkg_sum.GetHisto().GetBinContent(i + 1) -
                    histo.GetHisto().GetBinContent(i + 1))**2
        return res

    def get_errors(self, histname, histo):
        abs_err = r.TGraphAsymmErrors(histo.GetHisto())
        rel_err = r.TGraphAsymmErrors(histo.GetHisto())

        err_up = self.get_squared_bkg_shifts(self.__up, histname, histo)
        err_down = self.get_squared_bkg_shifts(self.__down, histname, histo)

        for i in range(histo.GetHisto().GetNbinsX()):
            bin_center = histo.GetHisto().GetBinCenter(i + 1)
            bin_content = histo.GetHisto().GetBinContent(i + 1)
            bin_error = histo.GetHisto().GetBinError(i + 1)
            bin_width = histo.GetHisto().GetBinWidth(i + 1)

            if bin_content > 0.001:
                rel_up = math.sqrt(err_up[i] + bin_error**2) / bin_content
                rel_down = math.sqrt(err_down[i] + bin_error**2) / bin_content
                # rel_up = math.sqrt(err_up[i]) / bin_content
                # rel_down = math.sqrt(err_down[i]) / bin_content
            else:
                rel_up = 0
                rel_down = 0

            abs_err.SetPoint(i, bin_center, bin_content)
            rel_err.SetPoint(i, bin_center, 1)

            abs_err.SetPointEXlow(i, bin_width / 2)
            abs_err.SetPointEXhigh(i, bin_width / 2)
            abs_err.SetPointEYlow(i, math.sqrt(err_down[i]))
            abs_err.SetPointEYhigh(i, math.sqrt(err_up[i]))

            rel_err.SetPointEXlow(i, bin_width / 2)
            rel_err.SetPointEXhigh(i, bin_width / 2)
            rel_err.SetPointEYlow(i, rel_down)
            rel_err.SetPointEYhigh(i, rel_up)
        return (abs_err, rel_err)

def to_ndc(x, y):
    new_x = r.gPad.GetLeftMargin() + x * (1 - r.gPad.GetLeftMargin() - r.gPad.GetRightMargin())
    new_y = r.gPad.GetBottomMargin() + y * (1 - r.gPad.GetBottomMargin() - r.gPad.GetTopMargin())
    return (new_x, new_y)

class Legend:
    def __init__(self, margin, ncols):
        self.__current = 0
        self.__box_dx = 0.06
        self.__box_dy = 0.04
        self.__legend_x = margin
        self.__legend_dx = (1. - 2 * margin) / ncols
        self.__legend_y = (1. - 0.5 * margin)
        self.__legend_dy = 1.4 * self.__box_dy
        self.__pos_x = self.__legend_x
        self.__pos_y = self.__legend_y

        self.__ncols = ncols

        self.__markers = []
        self.__paves = []
        self.__tex = r.TLatex()
        self.__tex.SetNDC()
        self.__tex.SetTextSize(0.035)
        self.__line = r.TLine()

    def advance(self):
        self.__current += 1
        self.__pos_x += self.__legend_dx
        if self.__current % self.__ncols == 0:
            self.__pos_x = self.__legend_x
            self.__pos_y -= self.__legend_dy

    def new_row(self):
        if self.__current % self.__ncols == 0:
            return
        self.__current = 0
        self.__pos_x = self.__legend_x
        self.__pos_y -= self.__legend_dy

    def draw_box(self, pattern, color, label, line=False):
        (x1, y1) = to_ndc(self.__pos_x, self.__pos_y)
        (x2, y2) = to_ndc(self.__pos_x + self.__box_dx, self.__pos_y - self.__box_dy)
        pave = r.TPave(x1, y1, x2, y2, 0, "NDC")
        pave.SetFillStyle(pattern)
        pave.SetFillColor(color)
        pave.SetBorderSize(0 if not line else 1)
        pave.Draw()
        self.__paves.append(pave)

        (text_x, text_y) = to_ndc(
                    self.__pos_x + 1.2 * self.__box_dx,
                    self.__pos_y - 0.8 * self.__box_dy)
        self.__tex.DrawLatex(text_x, text_y, label)
        self.advance()

    def draw_marker(self, style, color, label):
        self.__line.SetLineColor(color)
        self.__line.SetLineWidth(1)
        self.__line.DrawLineNDC(
                *(to_ndc(
                    self.__pos_x,
                    self.__pos_y - self.__box_dy / 2)
                + to_ndc(
                    self.__pos_x + self.__box_dx,
                    self.__pos_y - self.__box_dy / 2)))
        self.__line.DrawLineNDC(
                *(to_ndc(
                    self.__pos_x + self.__box_dx / 2,
                    self.__pos_y)
                + to_ndc(
                    self.__pos_x + self.__box_dx / 2,
                    self.__pos_y - self.__box_dy)))
        (marker_x, marker_y) = to_ndc(self.__pos_x + self.__box_dx / 2, self.__pos_y - self.__box_dy / 2)
        marker = r.TMarker(marker_x, marker_y, style)
        marker.SetMarkerStyle(style)
        marker.SetMarkerColor(color)
        marker.SetNDC()
        marker.Draw()
        self.__markers.append(marker)
        (text_x, text_y) = to_ndc(
                    self.__pos_x + 1.2 * self.__box_dx,
                    self.__pos_y - 0.8 * self.__box_dy)
        self.__tex.DrawLatex(text_x, text_y, label)
        self.advance()

    def draw_line(self, width, color, label):
        self.__line.SetLineColor(color)
        self.__line.SetLineWidth(width)
        self.__line.DrawLineNDC(
                *(to_ndc(
                    self.__pos_x,
                    self.__pos_y - self.__box_dy / 2)
                + to_ndc(
                    self.__pos_x + self.__box_dx,
                    self.__pos_y - self.__box_dy / 2)))
        (text_x, text_y) = to_ndc(
                    self.__pos_x + 1.2 * self.__box_dx,
                    self.__pos_y - 0.8 * self.__box_dy)
        self.__tex.DrawLatex(text_x, text_y, label)
        self.advance()

def stack(config, processes):
    procs = map(lambda n: get_process(n, processes), config['analysis']['plot'])

    err = SysErrors(config)

    plot_ratio = True

    padding = 0.001
    y_divide = 0.25
    ratio_plot_max = 2.5
    bottom_margin = 0.35
    small_number = 0.0001

    if config['display']['legend']:
        scale = 1.45
    else:
        scale = 1.15

    for histname in config['histograms'].keys():
        try:
            if all(map(lambda v: v <= 0, get_integrals(histname, procs))):
                logging.warn("empty histogram: %s", histname)
                continue
        except:
            logging.warn("unfilled histogram: %s", histname)
            continue

        logging.info("plotting %s", histname)

        bkg_procs = get_backgrounds(procs)
        bkg_stack = get_bkg_stack(histname, bkg_procs)
        bkg_stack.Draw("hist")

        max_y = scale * max(get_maximum(histname, procs, True),
                bkg_stack.GetMaximum())

        if plot_ratio:
            min_y = 0.002
            canvas = r.TCanvas(histname, histname, 800, 1000)
            canvas.Divide(1, 2)
            canvas.GetPad(1).SetPad(padding, y_divide + padding, 1 - padding, 1 - padding)
            canvas.GetPad(1).SetTopMargin(0.065)
            canvas.GetPad(1).SetBottomMargin(0)
            canvas.GetPad(2).SetPad(padding, padding, 1 - padding, y_divide - padding)
            canvas.GetPad(2).SetBottomMargin(bottom_margin)
            canvas.cd(1)
        else:
            min_y = 0.001
            canvas = r.TCanvas(histname, histname, 800, 800)
            canvas.cd()

        bkg_stack.Draw("hist")
        bkg_stack.SetMinimum(min_y)
        bkg_stack.SetMaximum(max_y)
        bkg_stack.GetYaxis().SetRangeUser(min_y, max_y)

        base_histo = roast.HWrapper(procs[0].GetHContainer()[histname])
        base_histo.ScaleBy(0)
        base_histo.GetHisto().SetTitle("")
        base_histo.GetHisto().GetYaxis().SetRangeUser(min_y, max_y)
        base_histo.GetHisto().GetXaxis().SetRangeUser(base_histo.GetMinXVis(), base_histo.GetMaxXVis())
        base_histo.GetHisto().Draw("hist")

        bkg_stack.Draw("hist same")

        bkg_sum = get_bkg_sum(histname, procs)
        bkg_sum.SetFillStyle(3654)
        bkg_sum.SetFillColor(r.kBlack)
        bkg_sum.SetMarkerStyle(0)
        # bkg_sum.GetHisto().Draw("E2 same")

        (abs_err, rel_err) = err.get_errors(histname, bkg_sum)
        abs_err.SetFillStyle(3654)
        abs_err.SetFillColor(r.kBlack)
        abs_err.SetMarkerStyle(0)
        abs_err.Draw("2 same")

        sig_procs = get_signals(procs)
        for p in sig_procs:
            h = p.GetHContainer()[histname].GetHisto()
            h.Scale(config['display']['signal scale factor'])
            h.SetFillStyle(0)
            h.SetLineWidth(3)
            h.SetLineColor(p.GetColor())
            h.GetYaxis().SetRangeUser(min_y, max_y)

            # FIXME implement stacking signals on top of bkg

            h.Draw("hist same")

        try:
            coll = get_collisions(procs)
            h = coll.GetHContainer()[histname].GetHisto()
            h.SetMarkerStyle(20)
            h.GetYaxis().SetRangeUser(min_y, max_y)
            h.SetLineWidth(2)
            h.Draw("E1 P same")
        except:
            coll = None
            # FIXME do something more sensible
            pass

        if config['display']['legend']:
            l = Legend(0.05, 3)
            for p in bkg_procs:
                l.draw_box(1001, p.GetColor(), p.GetLabelForLegend())
            l.draw_box(3654, r.kBlack, "Bkg. err.", True)
            if coll:
                l.draw_marker(20, r.kBlack, coll.GetLabelForLegend())
            l.new_row()
            for p in sig_procs:
                sig_scale = config['display']['signal scale factor']
                suffix = "" if sig_scale == 1 else " (#times {0})".format(sig_scale)
                l.draw_line(2, p.GetColor(), p.GetLabelForLegend() + suffix)

        base_histo.GetHisto().Draw("axis same")

        if plot_ratio:
            max_ratio = 2.5

            canvas.cd(2)

            try:
                ratio = coll.GetHContainer()[histname].GetHisto().Clone()
                ratio.Divide(bkg_sum.GetHisto())
            except:
                ratio = base_histo.GetHisto().Clone()

            ratio.GetXaxis().SetRangeUser(
                    bkg_sum.GetMinXVis(), bkg_sum.GetMaxXVis())

            ratio.GetXaxis().SetTitleSize(0.15)
            ratio.GetXaxis().SetLabelSize(0.1)
            ratio.GetYaxis().SetTitle("Data/MC")
            ratio.GetYaxis().CenterTitle()
            ratio.GetYaxis().SetTitleSize(0.15)
            ratio.GetYaxis().SetTitleOffset(0.4)
            ratio.GetYaxis().SetLabelSize(0.08)
            ratio.GetYaxis().SetRangeUser(min_y, max_ratio)
            ratio.Draw("axis")

            bkg_err = base_histo.GetHisto().Clone()
            for i in range(bkg_err.GetNbinsX()):
                bkg_err.SetBinContent(i + 1, 1)

                if bkg_sum.GetHisto().GetBinContent(i + 1) > 0.001:
                    bkg_err.SetBinError(i + 1,
                            bkg_sum.GetHisto().GetBinError(i + 1) /
                            bkg_sum.GetHisto().GetBinContent(i + 1))
                else:
                    bkg_err.SetBinError(i + 1, 0)
            bkg_err.SetMarkerSize(0)
            bkg_err.SetFillColor(r.kGreen)
            rel_err.SetMarkerSize(0)
            rel_err.SetFillColor(r.kGreen)
            rel_err.SetFillStyle(1001)
            if ratio:
                # bkg_err.Draw("E2 same")
                rel_err.Draw("2 same")
            else:
                # bkg_err.Draw("E2")
                rel_err.Draw("2")

            if coll:
                ratio_err = r.TGraphAsymmErrors(ratio)
                for i in range(ratio_err.GetN()):
                    x_coord = ratio.GetBinCenter(i + 1)
                    width = ratio.GetBinWidth(i + 1)
                    y_ratio = ratio.GetBinContent(i + 1)
                    y_data = coll.GetHContainer()[histname].GetHisto().GetBinContent(i + 1)
                    y_data_err = coll.GetHContainer()[histname].GetHisto().GetBinError(i + 1)
                    y_bkg = bkg_sum.GetHisto().GetBinContent(i + 1)

                    if y_ratio > small_number and y_ratio < ratio_plot_max * 0.99:
                        if y_bkg > small_number:
                            y_up = (y_data + y_data_err) / y_bkg
                            y_down = (y_data - y_data_err) / y_bkg
                        else:
                            y_up = 0
                            y_down = 0
                        ratio_err.SetPoint(i, x_coord, y_ratio)
                        ratio_err.SetPointEYhigh(i, y_up - y_ratio)
                        ratio_err.SetPointEYlow(i, y_ratio - y_down)
                        ratio_err.SetPointEXhigh(i, width / 2)
                        ratio_err.SetPointEXlow(i, width / 2)
                    else:
                        ratio_err.SetPoint(i, x_coord, 999)

                ratio_err.SetMarkerSize(1.)
                ratio_err.SetMarkerStyle(8)
                ratio_err.SetLineWidth(2)
                ratio_err.Draw("P same")
                ratio.Draw("axis same")

            line = r.TLine()
            line.SetLineColor(1)
            line.SetLineWidth(2)
            line.DrawLine(bkg_sum.GetMinXVis(), 1, bkg_sum.GetMaxXVis(), 1)

        filename = config['paths']['stack format'].format(t="png",
                d=base_histo.GetSubDir(), n=histname, m="")

        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        canvas.SaveAs(filename)

        # Reset log-scale maximum y-value
        new_max_y = 10 ** (((scale - 1) * 2 + 1) * math.log10(max_y / scale))
        canvas.cd(1)
        base_histo.GetHisto().GetYaxis().SetRangeUser(0.002, new_max_y)
        r.gPad.SetLogy()
        canvas.Update()

        filename = config['paths']['stack format'].format(t="png",
                d=base_histo.GetSubDir(), n=histname, m="_log")

        canvas.SaveAs(filename)
