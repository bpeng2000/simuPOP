/***************************************************************************
 *   Copyright (C) 2004 by Bo Peng                                         *
 *   bpeng@rice.edu                                                        *
 *                                                                         *
 *   $LastChangedDate: 2006-02-21 15:27:25 -0600 (Tue, 21 Feb 2006) $
 *   $Rev: 191 $
 *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
 ***************************************************************************/

#include "simupop_cfg.h"
#include "utility.h"
#include "recombinator.h"

namespace simuPOP
{
  void recombinator::prepareRecRates(population& pop,
    double intensity,
    vectorf rate,
    vectoru afterLoci,                            //
    bool sexChrom,                                // whether or not recombine the last chromosome
    vectoru& recBeforeLoci,                       // return before loci vector
    vectorf& vecP)                                // return recombination rate
  {
    if( !recBeforeLoci.empty() )
      return;

    DBG_FAILIF( intensity < 0 && rate.empty(), ValueError,
      "You should specify intensity, or rate "
      "(a number or a sequence of recombination rates.)");

    DBG_FAILIF( rate.size() > 1 && afterLoci.empty(), ValueError,
      "When more than one rates are given, afterLoci should be"
      " explicitly specified.");

    DBG_FAILIF( rate.size() > 1 && rate.size() != afterLoci.size(),
      ValueError,
      "If both rates and atLoci are specified, "
      "they should have the same length.");

    bool useLociDist;
    if( rate.empty() )                            // actually use intensity
      useLociDist = true;
    else
      useLociDist = false;

    // first, we create a recBeforeLoci vector
    // and a recombination rate vector
    if( afterLoci.empty())
    {
      size_t vecSize = pop.totNumLoci();
      if( sexChrom )
        vecSize -= pop.numLoci( pop.numChrom()-1) - 1;

      recBeforeLoci.resize(vecSize);
      for(size_t i=0; i<vecSize; ++i)
        recBeforeLoci[i] = i+1;
      // if sex chrom, the last one is the end of geno
      // instead of the beginning of the last chromosome
      recBeforeLoci[vecSize-1] = pop.totNumLoci();

      vecP.resize(vecSize );

      int index=0;
      UINT chEnd = pop.numChrom();

      for(UINT ch=0; ch < chEnd; ++ch)
      {
        // do we recombine the last chromosome?
        if( ch==chEnd-1 && sexChrom)
        {
          // the last one is used to determine the choice of
          // the first chromosome copy
          vecP[index] = 0.5;
          break;
        }

        /// get loci distance * rate and then recombinant points
        for( UINT loc = 0, locEnd=pop.numLoci(ch)-1;
          loc < locEnd; ++loc)
        {
          if(useLociDist)
            vecP[index] = (pop.locusPos(index+1) - pop.locusPos(index))*intensity;
          else
            vecP[index] = rate[0];

          DBG_ASSERT( fcmp_ge(vecP[index],0) && fcmp_le(vecP[index],1),
            ValueError,
            "Recombination rate should be in [0,1]. (This may happen \n"
            "when you use intensity instead of loci, and your loci \n"
            " distance is too high.)");
          index++;
        }
        // 'recombine' after each chromosome.
        vecP[index++] = .5;
      }

      // FIXME: remove zero indices for efficiency purpose, but there is no
      // real need for this if atLoci is not specified.

      DBG_DO(DBG_RECOMBINATOR, cout << "Use all Loci. With rates "
        << vecP << " before " << recBeforeLoci << endl);
    }
    else                                          // afterLoci not empty
    {
      DBG_FAILIF( rate.size() > 1 && rate.size() != afterLoci.size(), SystemError,
        "If an array is given, rates and afterLoci should have the same length");

      vectoru::iterator pos;
      vecP.clear();
      recBeforeLoci.clear();

      UINT index=0;

      for(UINT ch=0, chEnd = pop.numChrom(); ch < chEnd; ++ch)
      {
        if( ch == chEnd - 1 && sexChrom )
        {
          vecP.push_back(0.5);
          // this is meaningless.
          recBeforeLoci.push_back( pop.totNumLoci());
          break;
        }

        /// get loci distance * rate and then recombinant points
        for( UINT loc = 0, locEnd=pop.numLoci(ch)-1;
          loc < locEnd; ++loc)
        {
          // if this locus will be recombined.
          pos = find( afterLoci.begin(), afterLoci.end(), index);
          if( pos != afterLoci.end())
          {
            if( useLociDist )
            {
              if( intensity > 0 )                 // igore zero rate
              {
                vecP.push_back( (pop.locusPos(index+1) - pop.locusPos(index))*intensity);
                recBeforeLoci.push_back(index+1);
              }
            }
            else if( rate.size() == 1 && ! useLociDist)
            {
              if( rate[0] > 0 )                   // ignore zero rate
              {
                vecP.push_back( rate[0]);
                recBeforeLoci.push_back(index+1);
              }
            }
            else
            {
                                                  // ignore zero rate
              if( rate[ pos - afterLoci.begin() ] > 0 )
              {
                vecP.push_back( rate[ pos - afterLoci.begin() ] );
                recBeforeLoci.push_back(index+1);
              }
            }

            DBG_ASSERT( fcmp_ge(vecP[vecP.size()-1],0) && fcmp_le(vecP[vecP.size()-1],1),
              ValueError,
              "Recombination rate should be in [0,1]. (Maybe your loci distance is too high.)");
          }
          index++;
        }
        vecP.push_back(.5);

        if( find( afterLoci.begin(), afterLoci.end(), index) != afterLoci.end() )
          cout << "Specified recombination rate for the last locus on a chromosome is discarded." << endl;

        // add between chromosomes....
        index ++;
        recBeforeLoci.push_back(index);
      }

      // for debug purpose, check the original list:
      for(size_t i=0; i< afterLoci.size(); ++i)
      {
        DBG_FAILIF( find( recBeforeLoci.begin(), recBeforeLoci.end(), afterLoci[i]+1) == recBeforeLoci.end(),
          ValueError, "Specified locus " + toStr(afterLoci[i]) +
          " is not used in recombinator. Is it valid?");
      }

      DBG_ASSERT( vecP.size() == recBeforeLoci.size(), SystemError,
        "Rate and before loci should have the same length.");

      DBG_ASSERT( recBeforeLoci.back() == pop.totNumLoci(),
        SystemError, "The last beforeLoci elem should be total number of loci.");

      DBG_ASSERT( vecP.back() == .5, SystemError,
        "The last elem of rate should be half.");

      DBG_DO(DBG_RECOMBINATOR, cout << "Specify after Loci. With rates "
        << vecP << " before " << recBeforeLoci << endl);
    }

    /// initialize recombination counter,
    /// This will count recombination events after
    /// each locus.
    m_recCount.resize( pop.totNumLoci(), 0);
    return;
  }

  // this function implement how to recombine
  // parental chromosomes and set one copy of offspring chromosome
  // bt contains the bernulli trailer
  void  recombinator::recombine(
    individual* parent,                           // one of the parent
    population::IndIterator offspring,            // offspring
    int offPloidy,                                // which offspring ploidy to fill
    BernulliTrials& bt,
    const vectoru& recBeforeLoci,
    bool setSex)
  {
    // use which copy of chromosome
    GenoIterator cp[2], curCp, off;

    const BitSet& bs =  bt.trial();

    size_t sz = recBeforeLoci.size();

    int initCp = bs[sz-1]?0:1;

    // the last one does not count, because it determines
    // the initial copy of paternal chromosome
    const_cast<BitSet&>(bs).reset(sz-1);

    BitSet::size_type pos = bs.find_first();
    BitSet::size_type newpos = 0;

    // there is some recombination
    if(pos !=  BitSet::npos)
    {
      cp[0] = parent->genoBegin(0);
      cp[1] = parent->genoBegin(1);
      off = offspring->genoBegin(offPloidy);
      // make use of the last unused 1/2.
      curCp = cp[initCp];

      // copy from 0 to the first occurance
      copy(curCp, curCp+recBeforeLoci[pos], off);
      m_recCount[recBeforeLoci[pos]-1]++;

      // then switch to another chromosome copy
      curCp = (curCp == cp[0]) ? cp[1] : cp[0];

      // next ...
      while( (newpos = bs.find_next(pos)) != BitSet::npos )
      {
        // copy to offspring
        // element curCp+newpos+1 will not be copied. [) effect
        copy(curCp+recBeforeLoci[pos],
          curCp+recBeforeLoci[newpos],
          off+recBeforeLoci[pos]);
        m_recCount[recBeforeLoci[newpos]-1]++;
        pos = newpos;
        // switch
        curCp = (curCp == cp[0]) ? cp[1] : cp[0];
      }

      // copy the last piece
      // NOTE: we should make sure recBeforeLoci.back()
      // refer to the end of the chromosome

      copy(curCp + recBeforeLoci[pos],
        curCp + recBeforeLoci.back(),
        off + recBeforeLoci[pos]);

      if(setSex)
      {
        if( curCp == cp[0])
          offspring->setSex(Female);
        else
          offspring->setSex(Male);
      }
    }
    // if no switch is needed, copy the entire chromosome
    else
    {
      copy(parent->genoBegin(initCp),
        parent->genoEnd(initCp),
        offspring->genoBegin(offPloidy));

      if( setSex )
      {
        if( initCp == 0)                          // X of XY
          offspring->setSex(Female);
        else
          offspring->setSex(Male);
      }
    }                                             // no switch
  }

  bool  recombinator::applyDuringMating(population& pop,
    population::IndIterator offspring,
    individual* dad,
    individual* mom)
  {
    if( m_recBeforeLoci.empty() )
    {
      // prepare m_bt
      // female
      vectorf vecP;
      // female does not determine sex
      prepareRecRates(pop, m_intensity, m_rate, m_afterLoci,
        false, m_recBeforeLoci, vecP);
      m_bt.setParameter(vecP, pop.popSize()*pop.ploidy());

      vecP.clear();
      // male case is most complicated.
      m_setSex = pop.sexChrom()?true:false;
      double maleIntensity = (m_maleIntensity != -1 || !m_maleRate.empty() )
        ? m_maleIntensity : m_intensity;
      vectorf& maleRate = (m_maleIntensity != -1 || !m_maleRate.empty() )
        ? m_maleRate : m_rate;
      vectoru& maleAfterLoci = m_maleAfterLoci.empty()?
        m_afterLoci:m_maleAfterLoci;
      // prepare male recombination
      prepareRecRates(pop, maleIntensity, maleRate, maleAfterLoci,
        m_setSex, m_maleRecBeforeLoci, vecP);
      m_maleBt.setParameter(vecP, pop.popSize()*pop.ploidy());
    }

    recombine(mom, offspring, 0, m_bt, m_recBeforeLoci, false);
    recombine(dad, offspring, 1, m_maleBt,
      m_maleRecBeforeLoci, m_setSex);
    return true;
  }

}