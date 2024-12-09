//----------------------
// <auto-generated>
//     Generated using the NJsonSchema v10.9.0.0 (Newtonsoft.Json v13.0.0.0) (http://NJsonSchema.org)
// </auto-generated>
//----------------------


namespace AindBehaviorDeviceOlfactometer.TaskLogic
{
    #pragma warning disable // Disable all warnings

    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [Bonsai.CombinatorAttribute()]
    [Bonsai.WorkflowElementCategoryAttribute(Bonsai.ElementCategory.Source)]
    public partial class OlfactometerCalibrationParameters
    {
    
        private double? _rngSeed;
    
        private string _aindBehaviorServicesPkgVersion = "0.8.9";
    
        private System.Collections.Generic.IDictionary<string, OlfactometerChannelConfig> _channelConfig;
    
        private double _fullFlowRate = 1000D;
    
        private int _nRepeatsPerStimulus = 1;
    
        private double _timeOn = 1D;
    
        private double _timeOff = 1D;
    
        public OlfactometerCalibrationParameters()
        {
        }
    
        protected OlfactometerCalibrationParameters(OlfactometerCalibrationParameters other)
        {
            _rngSeed = other._rngSeed;
            _aindBehaviorServicesPkgVersion = other._aindBehaviorServicesPkgVersion;
            _channelConfig = other._channelConfig;
            _fullFlowRate = other._fullFlowRate;
            _nRepeatsPerStimulus = other._nRepeatsPerStimulus;
            _timeOn = other._timeOn;
            _timeOff = other._timeOff;
        }
    
        /// <summary>
        /// Seed of the random number generator
        /// </summary>
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("rng_seed")]
        [System.ComponentModel.DescriptionAttribute("Seed of the random number generator")]
        public double? RngSeed
        {
            get
            {
                return _rngSeed;
            }
            set
            {
                _rngSeed = value;
            }
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("aind_behavior_services_pkg_version")]
        public string AindBehaviorServicesPkgVersion
        {
            get
            {
                return _aindBehaviorServicesPkgVersion;
            }
            set
            {
                _aindBehaviorServicesPkgVersion = value;
            }
        }
    
        /// <summary>
        /// Configuration of olfactometer channels
        /// </summary>
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("channel_config")]
        [System.ComponentModel.DescriptionAttribute("Configuration of olfactometer channels")]
        public System.Collections.Generic.IDictionary<string, OlfactometerChannelConfig> ChannelConfig
        {
            get
            {
                return _channelConfig;
            }
            set
            {
                _channelConfig = value;
            }
        }
    
        /// <summary>
        /// Full flow rate of the olfactometer
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("full_flow_rate")]
        [System.ComponentModel.DescriptionAttribute("Full flow rate of the olfactometer")]
        public double FullFlowRate
        {
            get
            {
                return _fullFlowRate;
            }
            set
            {
                _fullFlowRate = value;
            }
        }
    
        /// <summary>
        /// Number of repeats per stimulus
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("n_repeats_per_stimulus")]
        [System.ComponentModel.DescriptionAttribute("Number of repeats per stimulus")]
        public int NRepeatsPerStimulus
        {
            get
            {
                return _nRepeatsPerStimulus;
            }
            set
            {
                _nRepeatsPerStimulus = value;
            }
        }
    
        /// <summary>
        /// Time (s) the valve is open during calibration
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("time_on")]
        [System.ComponentModel.DescriptionAttribute("Time (s) the valve is open during calibration")]
        public double TimeOn
        {
            get
            {
                return _timeOn;
            }
            set
            {
                _timeOn = value;
            }
        }
    
        /// <summary>
        /// Time (s) the valve is close during calibration
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("time_off")]
        [System.ComponentModel.DescriptionAttribute("Time (s) the valve is close during calibration")]
        public double TimeOff
        {
            get
            {
                return _timeOff;
            }
            set
            {
                _timeOff = value;
            }
        }
    
        public System.IObservable<OlfactometerCalibrationParameters> Process()
        {
            return System.Reactive.Linq.Observable.Defer(() => System.Reactive.Linq.Observable.Return(new OlfactometerCalibrationParameters(this)));
        }
    
        public System.IObservable<OlfactometerCalibrationParameters> Process<TSource>(System.IObservable<TSource> source)
        {
            return System.Reactive.Linq.Observable.Select(source, _ => new OlfactometerCalibrationParameters(this));
        }
    
        protected virtual bool PrintMembers(System.Text.StringBuilder stringBuilder)
        {
            stringBuilder.Append("rng_seed = " + _rngSeed + ", ");
            stringBuilder.Append("aind_behavior_services_pkg_version = " + _aindBehaviorServicesPkgVersion + ", ");
            stringBuilder.Append("channel_config = " + _channelConfig + ", ");
            stringBuilder.Append("full_flow_rate = " + _fullFlowRate + ", ");
            stringBuilder.Append("n_repeats_per_stimulus = " + _nRepeatsPerStimulus + ", ");
            stringBuilder.Append("time_on = " + _timeOn + ", ");
            stringBuilder.Append("time_off = " + _timeOff);
            return true;
        }
    
        public override string ToString()
        {
            System.Text.StringBuilder stringBuilder = new System.Text.StringBuilder();
            stringBuilder.Append(GetType().Name);
            stringBuilder.Append(" { ");
            if (PrintMembers(stringBuilder))
            {
                stringBuilder.Append(" ");
            }
            stringBuilder.Append("}");
            return stringBuilder.ToString();
        }
    }


    /// <summary>
    /// Harp Olfactometer available channel
    /// </summary>
    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    public enum OlfactometerChannel
    {
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="0")]
        Channel0 = 0,
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="1")]
        Channel1 = 1,
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="2")]
        Channel2 = 2,
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="3")]
        Channel3 = 3,
    }


    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [Bonsai.CombinatorAttribute()]
    [Bonsai.WorkflowElementCategoryAttribute(Bonsai.ElementCategory.Source)]
    public partial class OlfactometerChannelConfig
    {
    
        private int _channelIndex;
    
        private OlfactometerChannelType _channelType = AindBehaviorDeviceOlfactometer.TaskLogic.OlfactometerChannelType.Odor;
    
        private OlfactometerChannelConfigFlowRateCapacity _flowRateCapacity = AindBehaviorDeviceOlfactometer.TaskLogic.OlfactometerChannelConfigFlowRateCapacity._100;
    
        private double _flowRate = 100D;
    
        private string _odorant;
    
        private double? _odorantDilution;
    
        public OlfactometerChannelConfig()
        {
        }
    
        protected OlfactometerChannelConfig(OlfactometerChannelConfig other)
        {
            _channelIndex = other._channelIndex;
            _channelType = other._channelType;
            _flowRateCapacity = other._flowRateCapacity;
            _flowRate = other._flowRate;
            _odorant = other._odorant;
            _odorantDilution = other._odorantDilution;
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("channel_index", Required=Newtonsoft.Json.Required.Always)]
        public int ChannelIndex
        {
            get
            {
                return _channelIndex;
            }
            set
            {
                _channelIndex = value;
            }
        }
    
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("channel_type")]
        public OlfactometerChannelType ChannelType
        {
            get
            {
                return _channelType;
            }
            set
            {
                _channelType = value;
            }
        }
    
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("flow_rate_capacity")]
        public OlfactometerChannelConfigFlowRateCapacity FlowRateCapacity
        {
            get
            {
                return _flowRateCapacity;
            }
            set
            {
                _flowRateCapacity = value;
            }
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("flow_rate")]
        public double FlowRate
        {
            get
            {
                return _flowRate;
            }
            set
            {
                _flowRate = value;
            }
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("odorant")]
        public string Odorant
        {
            get
            {
                return _odorant;
            }
            set
            {
                _odorant = value;
            }
        }
    
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("odorant_dilution")]
        public double? OdorantDilution
        {
            get
            {
                return _odorantDilution;
            }
            set
            {
                _odorantDilution = value;
            }
        }
    
        public System.IObservable<OlfactometerChannelConfig> Process()
        {
            return System.Reactive.Linq.Observable.Defer(() => System.Reactive.Linq.Observable.Return(new OlfactometerChannelConfig(this)));
        }
    
        public System.IObservable<OlfactometerChannelConfig> Process<TSource>(System.IObservable<TSource> source)
        {
            return System.Reactive.Linq.Observable.Select(source, _ => new OlfactometerChannelConfig(this));
        }
    
        protected virtual bool PrintMembers(System.Text.StringBuilder stringBuilder)
        {
            stringBuilder.Append("channel_index = " + _channelIndex + ", ");
            stringBuilder.Append("channel_type = " + _channelType + ", ");
            stringBuilder.Append("flow_rate_capacity = " + _flowRateCapacity + ", ");
            stringBuilder.Append("flow_rate = " + _flowRate + ", ");
            stringBuilder.Append("odorant = " + _odorant + ", ");
            stringBuilder.Append("odorant_dilution = " + _odorantDilution);
            return true;
        }
    
        public override string ToString()
        {
            System.Text.StringBuilder stringBuilder = new System.Text.StringBuilder();
            stringBuilder.Append(GetType().Name);
            stringBuilder.Append(" { ");
            if (PrintMembers(stringBuilder))
            {
                stringBuilder.Append(" ");
            }
            stringBuilder.Append("}");
            return stringBuilder.ToString();
        }
    }


    /// <summary>
    /// Channel type
    /// </summary>
    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [Newtonsoft.Json.JsonConverter(typeof(Newtonsoft.Json.Converters.StringEnumConverter))]
    public enum OlfactometerChannelType
    {
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="Odor")]
        Odor = 0,
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="Carrier")]
        Carrier = 1,
    }


    /// <summary>
    /// Olfactometer operation control model that is used to run a calibration data acquisition workflow
    /// </summary>
    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [System.ComponentModel.DescriptionAttribute("Olfactometer operation control model that is used to run a calibration data acqui" +
        "sition workflow")]
    [Bonsai.CombinatorAttribute()]
    [Bonsai.WorkflowElementCategoryAttribute(Bonsai.ElementCategory.Source)]
    public partial class OlfactometerCalibrationLogic
    {
    
        private string _name = "OlfactometerCalibration";
    
        private string _description = "";
    
        private OlfactometerCalibrationParameters _taskParameters = new OlfactometerCalibrationParameters();
    
        private string _version = "0.1.0";
    
        private string _stageName;
    
        public OlfactometerCalibrationLogic()
        {
        }
    
        protected OlfactometerCalibrationLogic(OlfactometerCalibrationLogic other)
        {
            _name = other._name;
            _description = other._description;
            _taskParameters = other._taskParameters;
            _version = other._version;
            _stageName = other._stageName;
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("name")]
        public string Name
        {
            get
            {
                return _name;
            }
            set
            {
                _name = value;
            }
        }
    
        /// <summary>
        /// Description of the task.
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("description")]
        [System.ComponentModel.DescriptionAttribute("Description of the task.")]
        public string Description
        {
            get
            {
                return _description;
            }
            set
            {
                _description = value;
            }
        }
    
        [System.Xml.Serialization.XmlIgnoreAttribute()]
        [Newtonsoft.Json.JsonPropertyAttribute("task_parameters", Required=Newtonsoft.Json.Required.Always)]
        public OlfactometerCalibrationParameters TaskParameters
        {
            get
            {
                return _taskParameters;
            }
            set
            {
                _taskParameters = value;
            }
        }
    
        [Newtonsoft.Json.JsonPropertyAttribute("version")]
        public string Version
        {
            get
            {
                return _version;
            }
            set
            {
                _version = value;
            }
        }
    
        /// <summary>
        /// Optional stage name the `Task` object instance represents.
        /// </summary>
        [Newtonsoft.Json.JsonPropertyAttribute("stage_name")]
        [System.ComponentModel.DescriptionAttribute("Optional stage name the `Task` object instance represents.")]
        public string StageName
        {
            get
            {
                return _stageName;
            }
            set
            {
                _stageName = value;
            }
        }
    
        public System.IObservable<OlfactometerCalibrationLogic> Process()
        {
            return System.Reactive.Linq.Observable.Defer(() => System.Reactive.Linq.Observable.Return(new OlfactometerCalibrationLogic(this)));
        }
    
        public System.IObservable<OlfactometerCalibrationLogic> Process<TSource>(System.IObservable<TSource> source)
        {
            return System.Reactive.Linq.Observable.Select(source, _ => new OlfactometerCalibrationLogic(this));
        }
    
        protected virtual bool PrintMembers(System.Text.StringBuilder stringBuilder)
        {
            stringBuilder.Append("name = " + _name + ", ");
            stringBuilder.Append("description = " + _description + ", ");
            stringBuilder.Append("task_parameters = " + _taskParameters + ", ");
            stringBuilder.Append("version = " + _version + ", ");
            stringBuilder.Append("stage_name = " + _stageName);
            return true;
        }
    
        public override string ToString()
        {
            System.Text.StringBuilder stringBuilder = new System.Text.StringBuilder();
            stringBuilder.Append(GetType().Name);
            stringBuilder.Append(" { ");
            if (PrintMembers(stringBuilder))
            {
                stringBuilder.Append(" ");
            }
            stringBuilder.Append("}");
            return stringBuilder.ToString();
        }
    }


    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    public enum OlfactometerChannelConfigFlowRateCapacity
    {
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="100")]
        _100 = 100,
    
        [System.Runtime.Serialization.EnumMemberAttribute(Value="1000")]
        _1000 = 1000,
    }


    /// <summary>
    /// Serializes a sequence of data model objects into JSON strings.
    /// </summary>
    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [System.ComponentModel.DescriptionAttribute("Serializes a sequence of data model objects into JSON strings.")]
    [Bonsai.CombinatorAttribute()]
    [Bonsai.WorkflowElementCategoryAttribute(Bonsai.ElementCategory.Transform)]
    public partial class SerializeToJson
    {
    
        private System.IObservable<string> Process<T>(System.IObservable<T> source)
        {
            return System.Reactive.Linq.Observable.Select(source, value => Newtonsoft.Json.JsonConvert.SerializeObject(value));
        }

        public System.IObservable<string> Process(System.IObservable<OlfactometerCalibrationParameters> source)
        {
            return Process<OlfactometerCalibrationParameters>(source);
        }

        public System.IObservable<string> Process(System.IObservable<OlfactometerChannelConfig> source)
        {
            return Process<OlfactometerChannelConfig>(source);
        }

        public System.IObservable<string> Process(System.IObservable<OlfactometerCalibrationLogic> source)
        {
            return Process<OlfactometerCalibrationLogic>(source);
        }
    }


    /// <summary>
    /// Deserializes a sequence of JSON strings into data model objects.
    /// </summary>
    [System.CodeDom.Compiler.GeneratedCodeAttribute("Bonsai.Sgen", "0.4.0.0 (Newtonsoft.Json v13.0.0.0)")]
    [System.ComponentModel.DescriptionAttribute("Deserializes a sequence of JSON strings into data model objects.")]
    [System.ComponentModel.DefaultPropertyAttribute("Type")]
    [Bonsai.WorkflowElementCategoryAttribute(Bonsai.ElementCategory.Transform)]
    [System.Xml.Serialization.XmlIncludeAttribute(typeof(Bonsai.Expressions.TypeMapping<OlfactometerCalibrationParameters>))]
    [System.Xml.Serialization.XmlIncludeAttribute(typeof(Bonsai.Expressions.TypeMapping<OlfactometerChannelConfig>))]
    [System.Xml.Serialization.XmlIncludeAttribute(typeof(Bonsai.Expressions.TypeMapping<OlfactometerCalibrationLogic>))]
    public partial class DeserializeFromJson : Bonsai.Expressions.SingleArgumentExpressionBuilder
    {
    
        public DeserializeFromJson()
        {
            Type = new Bonsai.Expressions.TypeMapping<OlfactometerCalibrationLogic>();
        }

        public Bonsai.Expressions.TypeMapping Type { get; set; }

        public override System.Linq.Expressions.Expression Build(System.Collections.Generic.IEnumerable<System.Linq.Expressions.Expression> arguments)
        {
            var typeMapping = (Bonsai.Expressions.TypeMapping)Type;
            var returnType = typeMapping.GetType().GetGenericArguments()[0];
            return System.Linq.Expressions.Expression.Call(
                typeof(DeserializeFromJson),
                "Process",
                new System.Type[] { returnType },
                System.Linq.Enumerable.Single(arguments));
        }

        private static System.IObservable<T> Process<T>(System.IObservable<string> source)
        {
            return System.Reactive.Linq.Observable.Select(source, value => Newtonsoft.Json.JsonConvert.DeserializeObject<T>(value));
        }
    }
}