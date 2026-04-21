using Bonsai;
using System;
using System.ComponentModel;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Linq;
using AindBehaviorDeviceOlfactometerDataSchema;

[Combinator]
[Description("Creates an array of one-hot encoded concentration values for each olfactometer channel.")]
[WorkflowElementCategory(ElementCategory.Transform)]
public class CreateOneHotConcentrationArray
{
    private int channelNumber = 3;
    public int ChannelNumber
    {
        get { return channelNumber; }
        set { channelNumber = value; }
    }

    private double concentration = 1.0;
    public double Concentration
    {
        get { return concentration; }
        set { concentration = value; }
    }
    
    public IObservable<List<double>> Process(IObservable<OlfactometerChannel> source)
    {
        return source.Select(value =>
        {
            var oneHotArray = new List<double>(new double[channelNumber]);
            oneHotArray[channelNumber] = concentration;
            return oneHotArray;
        });
    }

    public IObservable<List<double>> Process(IObservable<int> source)
    {
        return Process(source);
    }
}
