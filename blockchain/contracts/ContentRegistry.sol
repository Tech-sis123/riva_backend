// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ContentRegistry {
    struct Content {
        address creator;
        string hash;
        uint256 timestamp;
    }

    mapping(string => Content) public contents;

    event ContentRegistered(address indexed creator, string hash, uint256 timestamp);

    function registerContent(string memory _hash) public {
        require(contents[_hash].timestamp == 0, "Content already registered");

        contents[_hash] = Content({
            creator: msg.sender,
            hash: _hash,
            timestamp: block.timestamp
        });

        emit ContentRegistered(msg.sender, _hash, block.timestamp);
    }

    function getContent(string memory _hash) public view returns (Content memory) {
        return contents[_hash];
    }
}
