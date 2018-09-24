import React, { Component } from 'react';
import { render } from 'react-dom';

import { Button } from 'antd';

import '../CSS/main.css';
import '../CSS/puzzle.css';

export default class Puzzle extends Component {
    constructor() {
        super();
        this.state = {
            fill: "empty"
        }
    }


    returnBoxes() {
        let i;
        let boxes = [];
        for (i = 0; i < 100; i++) {
            var fill = "";
            i%3 == 0? fill = "filled": fill = "empty";
            boxes.push(<div key={i} id={"item" + (i + 1)} className={fill}><input id="item1-1" type="text" maxLength="1" /></div>)
        }
        return boxes;
    }

    render() {
        return (
            <div id="wrapper">
                {this.returnBoxes()}
            </div>
        )

    }
}