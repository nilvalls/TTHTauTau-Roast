// vim: ts=4:sw=4:et:sta
#include <iomanip>

#include "boost/lexical_cast.hpp"

#include "../interface/Helper.h"
#include "../interface/Process.h"

using namespace std;
using namespace roast;

Process::Process()
{
   analyzed			= false;
   goodEvents.clear();
   plot				= false;
}

Process::Process(const Process& iProcess){

	goodEvents				= iProcess.GetGoodEvents();

    for (auto& pair: hContainer)
        delete pair.second;

    for (auto& pair: iProcess.GetHContainer())
        hContainer[pair.first] = new HWrapper(*pair.second);

	cutFlow							= CutFlow(*iProcess.GetConstCutFlow());
	normalizedCutFlow				= CutFlow(*iProcess.GetNormalizedCutFlow());

	shortName						= iProcess.GetShortName();
	niceName						= iProcess.GetNiceName();
	labelForLegend					= iProcess.GetLabelForLegend();
	type							= iProcess.GetType();
   treename = iProcess.GetTreeName();
	checkReality					= iProcess.CheckReality();
	ntuplePaths						= iProcess.GetNtuplePaths();
	color							= iProcess.GetColor();

	crossSection					= iProcess.GetCrossSection();
	branchingRatio					= iProcess.GetBranchingRatio();
	otherScaleFactor				= iProcess.GetOtherScaleFactor();
    relSysUncertainty               = iProcess.GetRelSysUncertainty();

	analyzed						= iProcess.Analyzed();
	NOEinDS							= iProcess.GetNOEinDS();
	NoEreadByNUTter					= iProcess.GetNoEreadByNUTter();
	NOEinNtuple						= iProcess.GetNOEinNtuple();
	NOEanalyzed						= iProcess.GetNOEanalyzed();
	NOEexpected			= iProcess.GetNOEexpected();
	plot							= iProcess.Plot();

	obtainedGoodEvents		= iProcess.ObtainedGoodEvents();
	filledHistos			= iProcess.FilledHistos();
	normalizedHistos		= iProcess.NormalizedHistos();

}

Process::Process(const std::string& name, const std::string& alias, const std::string& title,
      const std::string& type, const std::string& tree, const std::vector<std::string>& paths, int color,
      int ds_count, int nut_count, double xsec, double branch, bool genmatch):
   goodEvents(),
   shortName(name),
   niceName(alias),
   labelForLegend(title),
   type(type),
   treename(tree),
   checkReality(genmatch),
   ntuplePaths(paths),
   color(color),
   analyzed(false),
   plot(false),
   crossSection(xsec),
   branchingRatio(branch),
   otherScaleFactor(1.),
   NOEinDS(ds_count),
   NoEreadByNUTter(nut_count),
   NOEanalyzed(0),
   NOEexpected(0),
   obtainedGoodEvents(false),
   filledHistos(false),
   normalizedHistos(false),
   relSysUncertainty(0.)
{
}

Process::~Process()
{
    for (auto& pair: hContainer)
        delete pair.second;
}

// Update process
void Process::Update(Process const * iProcess){

   treename = iProcess->GetTreeName();
	niceName						= iProcess->GetNiceName();
	labelForLegend					= iProcess->GetLabelForLegend();
	type							= iProcess->GetType();
	checkReality					= iProcess->CheckReality();
	color							= iProcess->GetColor();

	crossSection					= iProcess->GetCrossSection();
	branchingRatio					= iProcess->GetBranchingRatio();
	otherScaleFactor				= iProcess->GetOtherScaleFactor();
    relSysUncertainty               = iProcess->GetRelSysUncertainty();

	plot							= iProcess->Plot();

	normalizedHistos		= false;

	// Update cutflow
	cutFlow.SetCutCounts("Read from DS", iProcess->GetNOEinDS());
	cutFlow.SetCutCounts("skimming + PAT", iProcess->GetNoEreadByNUTter());
	
}


vector<Process::Event> const Process::GetGoodEvents() const { return goodEvents; }
void Process::SetCutFlow(CutFlow const & iCutFlow){ cutFlow	= CutFlow(iCutFlow); }
void Process::SetNormalizedCutFlow(CutFlow const & iCutFlow){ normalizedCutFlow	= CutFlow(iCutFlow); }
void Process::SetNOEanalyzed(double const iEvents){ NOEanalyzed = iEvents; }
void Process::SetNOEinNtuple(double const iEvents){ NOEinNtuple = iEvents; }
void Process::SetRelSysUncertainty(double const iError){ relSysUncertainty = iError; }
void Process::SetColor(int const iColor){ color = iColor; }
CutFlow* Process::GetCutFlow() { return &cutFlow; }
CutFlow const * Process::GetConstCutFlow() const { return &cutFlow; }
CutFlow* Process::GetNormalizedCutFlow() { return &normalizedCutFlow; }
CutFlow const * Process::GetNormalizedCutFlow() const { return &normalizedCutFlow; }
string const Process::GetShortName() const {	return shortName;		}
string const Process::GetNiceName() const {			return niceName;		}
string const Process::GetLabelForLegend() const {	return labelForLegend;	}
string const Process::GetType() const {				return type;			}
bool const Process::IsMC() const { return ((type.compare("mcBackground")==0) || (type.compare("signal")==0)); }
bool const Process::Plot() const { return plot; }
void Process::SetNtuplePaths(vector<string> const iPath){ ntuplePaths = iPath; }

bool const Process::IsCollisions() const { return ((type.compare("collisions")==0)); }
bool const Process::IsBackground() const { return ((type.compare("mcBackground")==0)); }
bool const Process::IsSignal() const { return ((type.compare("signal")==0)); }
bool const Process::CheckReality() const { return checkReality; }
vector<string> const Process::GetNtuplePaths() const { return ntuplePaths; }
int const Process::GetColor() const { return color; }
int const Process::GetNOEinDS() const {			return NOEinDS;		}
int const Process::GetNoEreadByNUTter() const {	return NoEreadByNUTter;}
int const Process::GetNOEinNtuple() const {		return NOEinNtuple; }
int const Process::GetNOEanalyzed() const {		return NOEanalyzed; }

double const Process::GetCrossSection() const{ return crossSection;}
double const Process::GetBranchingRatio() const{ return branchingRatio;}
double const Process::GetOtherScaleFactor() const{ return otherScaleFactor;}
double const Process::GetNOEexpected() const{ return NOEexpected;}
double const Process::GetRelSysUncertainty() const{ return relSysUncertainty;}
bool const Process::ObtainedGoodEvents() const{ return obtainedGoodEvents;}
bool const Process::FilledHistos() const{ return filledHistos;}
bool const Process::NormalizedHistos() const{ return normalizedHistos;}


void Process::SetShortName(string const iVal){ 
	shortName = iVal;
}
void Process::SetNiceName(string const iVal){ niceName = iVal; }
void Process::SetLabelForLegend(string const iVal){ labelForLegend = iVal; }
void Process::SetAnalyzed(){ analyzed = true; }
bool const Process::Analyzed() const { return analyzed; }

void
Process::ResetHistograms()
{
    for (auto& pair: hContainer)
        if (pair.second->GetHisto())
            pair.second->GetHisto()->Reset("M");
}

void
Process::ScaleHistograms(double factor)
{
    for (auto& pair: hContainer)
        if (pair.second->GetHisto())
            pair.second->ScaleBy(factor);
}

std::vector<std::string>
Process::GetHistogramNames() const
{
    vector<string> res;
    for (const auto& pair: hContainer)
        res.push_back(pair.first);
    return res;
}

// Massive set histogram properties
void Process::SetGoodEvents(const vector<Process::Event>& iVector){ goodEvents = iVector; }


void
Process::NormalizeToLumi(double const iIntLumi)
{
	if ((!IsCollisions()) && (!normalizedHistos)) {
		double NOElumi				= iIntLumi*crossSection*branchingRatio;
		double NOEraw				= GetNOEinDS()*(GetNOEanalyzed()/(double)GetNOEinNtuple());	
		double lumiNormalization	= NOElumi/NOEraw;
		lumiNormalization 			*= GetOtherScaleFactor();
		cout << setprecision(7) << "\n" << shortName << " normalization: \n" 
			<< "\t---------------------------------------\n"
			<< "\tintLumi...." << iIntLumi << "\n" 
			<< "\tcrossSec..." << crossSection << "\n" 
			<< "\tBR............" << branchingRatio << "\n" 
			<< "\tNOEinDS......." << GetNOEinDS() << "\n" 
			<< "\tNOEanalyzed..." << GetNOEanalyzed() << "\n" 
			<< "\tNOEinNtuple..." << GetNOEinNtuple() << "\n" 
			<< "\t---------------------------------------\n"
			<< "\tNOElumi......." << NOElumi << "\n" 
			<< "\tNOEraw........" << NOEraw << "\n" 
			<< "\tOtherSF......." << GetOtherScaleFactor() << "\n" 
			<< "\t---------------------------------------\n"
			<< "\tSF............" << lumiNormalization << "\n" 
			<< "\trelSysSuncertainty....." << relSysUncertainty*100 << "%" << "\n" << endl; //*/

        ScaleHistograms(lumiNormalization);
		GetCutFlow()->RegisterCutFromLast("Lumi norm", 2, lumiNormalization);

      // FIXME
        // hContainer.AddRelErrorInQuadrature(relSysUncertainty);
	}
	normalizedHistos	= true;
}

void Process::BuildNormalizedCutFlow(){ normalizedCutFlow.BuildNormalizedCutFlow(&cutFlow); }

void Process::Add(Process* iProcess){
    for (const auto& p: iProcess->GetNtuplePaths())
        ntuplePaths.push_back(p);
    for (auto& pair: hContainer)
        pair.second->Add(*iProcess->GetHContainer()[pair.first]->GetHisto());
	cutFlow.Add(*(iProcess->GetCutFlow()));
	normalizedCutFlow.Add(*(iProcess->GetNormalizedCutFlow()));
}

ClassImp(roast::Process)
ClassImp(roast::Process::Event)
